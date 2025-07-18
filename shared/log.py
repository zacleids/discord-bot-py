import contextvars
import inspect
import json
import logging
import sys
import time
import uuid
from functools import wraps
from logging.handlers import RotatingFileHandler
from typing import Any, Awaitable, Callable

import discord
from flask import jsonify, request

from .config import config


# --- JsonFormatter for structured logging ---
class JsonFormatter(logging.Formatter):
    def format(self, record):
        # If the message is already a dict, use it; else, wrap as dict
        if isinstance(record.msg, dict):
            log_record = record.msg.copy()
        else:
            log_record = {"message": record.getMessage()}
        log_record["log_level"] = record.levelname  # Add log_level key
        log_record["time"] = self.formatTime(record, self.datefmt)
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)


# --- Logger setup (file + console, JSON if possible) ---
logger = logging.getLogger("discord_bot")
logger.setLevel(getattr(logging, config.log_level, logging.INFO))
logger.propagate = False  # Prevent propagation to root logger
formatter = JsonFormatter()

# Use RotatingFileHandler for log rotation (5MB per file, 3 backups)
file_handler = RotatingFileHandler("bot.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
file_handler.setFormatter(formatter)
if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
    logger.addHandler(file_handler)

# Only add a StreamHandler for the console if one does not already exist (excluding FileHandler)
if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in logger.handlers):
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# --- Context variable for ray id ---
ray_id_var = contextvars.ContextVar("ray_id", default=None)


def get_ray_id():
    ray_id = ray_id_var.get()
    if ray_id is None:
        ray_id = str(uuid.uuid4())
        ray_id_var.set(ray_id)
    return ray_id


async def with_ray_id(func, *args, **kwargs):
    ray_id = str(uuid.uuid4())
    token = ray_id_var.set(ray_id)
    try:
        return await func(*args, **kwargs)
    finally:
        ray_id_var.reset(token)


def log_event(event_type, context={}, level="INFO"):
    """
    Log an event with a given type and context dict, using structured logging.
    Automatically adds a UTC ISO8601 timestamp.
    """
    level = level.upper()
    log_data = {"event": event_type, **context}
    log_data["log_level"] = level  # Add log_level key at top level
    if level == "INFO":
        logger.info(log_data)
    elif level == "WARNING":
        logger.warning(log_data)
    elif level == "ERROR":
        logger.error(log_data)
    else:
        logger.debug(log_data)


def log_and_send_message_command(message, content=None, *, files=None, exec_time=None, **kwargs):
    """
    Helper to log outgoing message command responses and send the message.
    Logs content, files, ray id, and execution time, then sends the message.
    """
    ray_id = get_ray_id()
    log_context = {
        "ray_id": ray_id,
        "event": "OUTGOING_MESSAGE_COMMAND",
        "message_id": getattr(message, "id", None),
        "channel_id": getattr(message.channel, "id", None),
        "guild_id": getattr(message.guild, "id", None) if message.guild else None,
        "user_id": getattr(message.author, "id", None),
        "content": content,
        "file_count": len(files) if files else 0,
        "exec_time": exec_time,
    }
    log_event("OUTGOING_COMMAND", log_context)
    # Performance warning for slow message commands
    if exec_time is not None and exec_time > config.performance_warning_threshold:
        log_event(
            "PERFORMANCE_WARNING",
            {
                "ray_id": ray_id,
                "event": "PERFORMANCE_WARNING",
                "command_type": "message_command",
                "exec_time": exec_time,
                "performance_warning_threshold": config.performance_warning_threshold,
                "message_id": getattr(message, "id", None),
                "channel_id": getattr(message.channel, "id", None),
                "guild_id": getattr(message.guild, "id", None) if message.guild else None,
                "user_id": getattr(message.author, "id", None),
                "content": content,
            },
            level="warning",
        )
    if files:
        return message.channel.send(content, files=files, **kwargs)
    else:
        return message.channel.send(content, **kwargs)


def log_and_send_message_interaction(interaction: discord.Interaction, content=None, *, files=None, exec_time=None, **kwargs):
    """
    Helper to log outgoing interaction (slash command) responses and send the message.
    Logs content, files, ray id, and execution time, then sends the message.
    """
    ray_id = get_ray_id()
    embeds = kwargs.get("embeds", [])
    embed_log = [e.to_dict() if hasattr(e, "to_dict") else str(e) for e in embeds] if embeds else []
    embed = kwargs.get("embed", None)
    if embed:
        embed_log.append(embed.to_dict() if hasattr(embed, "to_dict") else str(embed))
    # Ensure files is always a list (never None)
    files = files if files is not None else []
    log_context = {
        "ray_id": ray_id,
        "event": "OUTGOING_SLASH_COMMAND",
        "interaction_id": getattr(interaction, "id", None),
        "channel_id": getattr(interaction.channel, "id", None),
        "guild_id": getattr(interaction.guild, "id", None) if interaction.guild else None,
        "user_id": getattr(interaction.user, "id", None),
        "content": content,
        "embeds": embed_log,
        "file_count": len(files),
        "exec_time": exec_time,
    }
    log_event("OUTGOING_INTERACTION", log_context)
    # Use response.send_message if not responded, else followup.send
    if not interaction.response.is_done():
        return interaction.response.send_message(content, files=files, **kwargs)
    else:
        return interaction.followup.send(content, files=files, **kwargs)


def log_interaction(func: Callable[..., Awaitable[None]]) -> Callable[..., Awaitable[None]]:
    import functools

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> None:
        # Extract the interaction object
        interaction = None
        for arg in args:
            if isinstance(arg, discord.Interaction):
                interaction = arg
                break

        ray_id = get_ray_id()
        start_time = time.perf_counter()
        if interaction:
            server_name = interaction.guild.name if interaction.guild else "DM"
            server_id = interaction.guild.id if interaction.guild else None
            if hasattr(interaction.channel, "name"):
                channel_name = interaction.channel.name
                channel_id = getattr(interaction.channel, "id", None)
            else:
                channel_name = f"DM with {interaction.user.name}"
                channel_id = None
            user_name = interaction.user.name
            user_id = interaction.user.id
            command_path = f"/{interaction.command.qualified_name}" if interaction.command else ""

            # Try to serialize args and kwargs as JSON, fallback to str if not possible
            def try_json(obj):
                try:
                    json.dumps(obj, ensure_ascii=False)
                    return obj
                except Exception:
                    return str(obj)

            args_json = try_json(args[1:])  # Skip the first arg (interaction itself)
            kwargs_json = try_json(kwargs)
            interaction_id = getattr(interaction, "id", None)
            locale = getattr(interaction, "locale", None)
            log_context = {
                "ray_id": ray_id,
                "event": "INCOMING_SLASH_COMMAND",
                "interaction_id": interaction_id,
                "channel_id": channel_id,
                "guild_id": server_id,
                "user_id": user_id,
                "user": user_name,
                "guild": server_name,
                "channel": channel_name,
                "command": command_path,
                "args": args_json,
                "kwargs": kwargs_json,
                "locale": locale,
                "function": func.__name__,
            }
            log_event("INCOMING_INTERACTION", log_context)
        else:
            log_event(
                "INCOMING_INTERACTION",
                {"ray_id": ray_id, "event": "INCOMING_SLASH_COMMAND", "interaction_id": None, "function": func.__name__},
            )
        try:
            await func(*args, **kwargs)
        finally:
            exec_time = time.perf_counter() - start_time
            log_event(
                "EXECUTION_TIME",
                {
                    "ray_id": ray_id,
                    "event": "SLASH_COMMAND_EXECUTION_TIME",
                    "interaction_id": getattr(interaction, "id", None) if interaction else None,
                    "function": func.__name__,
                    "exec_time": exec_time,
                },
            )
            # Performance warning for slow slash commands
            if exec_time > config.performance_warning_threshold:
                log_event(
                    "PERFORMANCE_WARNING",
                    {
                        "ray_id": ray_id,
                        "event": "PERFORMANCE_WARNING",
                        "command_type": "slash_command",
                        "exec_time": exec_time,
                        "performance_warning_threshold": config.performance_warning_threshold,
                        "interaction_id": getattr(interaction, "id", None) if interaction else None,
                        "function": func.__name__,
                    },
                    level="warning",
                )

    wrapper.__signature__ = inspect.signature(func)
    return wrapper


def log_and_send_json_response(response, *, status_code=200, extra_context=None):
    """
    Helper to log outgoing Flask JSON responses and return the response.
    Logs the response data, status code, and ray id.
    """
    ray_id = get_ray_id()
    log_context = {
        "ray_id": ray_id,
        "event": "OUTGOING_WEB_RESPONSE",
        "method": request.method,
        "url": request.url,
        "path": request.path,
        "remote_addr": request.remote_addr,
        "status_code": status_code,
        "response": response,
    }
    if extra_context:
        log_context.update(extra_context)
    log_event("OUTGOING_WEB_RESPONSE", log_context)
    return jsonify(response), status_code


def log_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ray_id = get_ray_id()
        log_context = {
            "ray_id": ray_id,
            "event": "INCOMING_WEB_REQUEST",
            "method": request.method,
            "url": request.url,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "headers": dict(request.headers),
            "args": request.args.to_dict(),
            "form": request.form.to_dict(),
            "json": request.get_json(silent=True),
            "client_ip": request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr),
        }
        log_event("INCOMING_WEB_REQUEST", log_context)
        start_time = time.perf_counter()
        try:
            return f(*args, **kwargs)
        finally:
            exec_time = time.perf_counter() - start_time
            log_event(
                "EXECUTION_TIME",
                {
                    "ray_id": ray_id,
                    "event": "WEB_REQUEST_EXECUTION_TIME",
                    "method": request.method,
                    "url": request.url,
                    "path": request.path,
                    "exec_time": exec_time,
                },
            )
            if exec_time > config.performance_warning_threshold:
                log_event(
                    "PERFORMANCE_WARNING",
                    {
                        "ray_id": ray_id,
                        "event": "PERFORMANCE_WARNING",
                        "command_type": "web_request",
                        "exec_time": exec_time,
                        "performance_warning_threshold": config.performance_warning_threshold,
                        "method": request.method,
                        "url": request.url,
                        "path": request.path,
                    },
                    level="warning",
                )

    return decorated_function


# After logger setup, flush any buffered config log events
config.flush_log_buffer()
