from typing import Callable, Awaitable, Any
import discord
import inspect
import logging
import uuid
import contextvars

# Only get the logger, do not add handlers here!
logger = logging.getLogger("discord_bot")

# Context variable for ray id
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

def log_and_send_message(interaction: discord.Interaction, *args, **kwargs):
    """
    Helper to log outgoing interaction responses and send the message.
    Logs content, embeds, file attachments, and ray id, then calls send_message or followup.send as appropriate.
    """
    content = args[0] if args else kwargs.get("content", "")
    embeds = kwargs.get("embeds", [])
    embed_log = ""
    if embeds:
        embed_log = f", Embeds: {[e.to_dict() if hasattr(e, 'to_dict') else str(e) for e in embeds]}"
    embed = kwargs.get("embed", None)
    if embed:
        embed_log += f", Embed: {embed.to_dict() if hasattr(embed, 'to_dict') else str(embed)}"
    files = kwargs.get("files", None)
    if files:
        file_log = f", Files: {len(files)} attached"
    else:
        file_log = ""
    ray_id = get_ray_id()
    logger.info(f"[ray_id={ray_id}] Interaction response: {content}{embed_log}{file_log}".replace("\n", "\\n").replace("\r", "\\r"))
    # Use response.send_message if not responded, else followup.send
    if not interaction.response.is_done():
        return interaction.response.send_message(*args, **kwargs)
    else:
        return interaction.followup.send(*args, **kwargs)


def log_interaction(func: Callable[..., Awaitable[None]]) -> Callable[..., Awaitable[None]]:
    import functools
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> None:
        import time
        # Extract the interaction object
        interaction = None
        for arg in args:
            if isinstance(arg, discord.Interaction):
                interaction = arg
                break

        ray_id = get_ray_id()
        log_message = ""
        start_time = time.perf_counter()
        # If interaction is found, log its details
        if interaction:
            server_name = interaction.guild.name if interaction.guild else "DM"
            server_id = interaction.guild.id if interaction.guild else None
            # Safely get channel name or DM info
            if hasattr(interaction.channel, "name"):
                channel_name = interaction.channel.name
                channel_id = getattr(interaction.channel, 'id', None)
            else:
                channel_name = f"DM with {interaction.user.name}"
                channel_id = None
            user_name = interaction.user.name
            user_id = interaction.user.id
            command_path = f"/{interaction.command.qualified_name}" if interaction.command else ""
            args_str = str(args[1:])
            kwargs_str = str(kwargs)
            interaction_id = getattr(interaction, 'id', None)
            locale = getattr(interaction, 'locale', None)
            log_message = (
                f"[ray_id={ray_id}] / interaction | {command_path} | "
                f"Server: {server_name} ({server_id}), Channel: {channel_name} ({channel_id}), Author: {user_name} ({user_id}), "
                f"Args: {args_str}, Kwargs: {kwargs_str}, InteractionID: {interaction_id}, Locale: {locale}, Function: {func.__name__}"
            )
        else:
            log_message = f"[ray_id={ray_id}] / interaction | No interaction object found | Function: {func.__name__}"

        logger.info(log_message.replace("\n", "\\n").replace("\r", "\\r"))
        try:
            await func(*args, **kwargs)
        finally:
            exec_time = time.perf_counter() - start_time
            logger.info(f"[ray_id={ray_id}] / interaction | ExecutionTime: {exec_time:.3f}s | Function: {func.__name__}")

    wrapper.__signature__ = inspect.signature(func)
    # Use functools.wraps and return the wrapper directly (do not wrap with lambda)
    return wrapper
