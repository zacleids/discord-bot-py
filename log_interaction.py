from typing import Callable, Awaitable, Any
import discord
import inspect


def log_interaction(func: Callable[..., Awaitable[None]]) -> Callable[..., Awaitable[None]]:
    async def wrapper(*args: Any, **kwargs: Any) -> None:
        # Extract the interaction object
        interaction = None
        for arg in args:
            if isinstance(arg, discord.Interaction):
                interaction = arg
                break

        log_message = ""

        # If interaction is found, log its details
        if interaction:
            server_name = interaction.guild.name if interaction.guild else "DM"
            # Safely get channel name or DM info
            if hasattr(interaction.channel, "name"):
                channel_name = interaction.channel.name
            else:
                channel_name = f"DM with {interaction.user.name}"
            user_name = interaction.user.name
            log_message = f"/ interaction \t| Server: {server_name}, Channel: {channel_name}, Author: {user_name}"

        log_message = log_message + f", args: {args[1:]}, function: {func.__name__}, kwargs: {kwargs}"

        print(log_message)

        # Dynamically call the original function with all arguments
        await func(*args, **kwargs)

    # Preserve the original function's signature
    wrapper.__signature__ = inspect.signature(func)
    return wrapper
