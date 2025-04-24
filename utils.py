import re
import functools
import discord


def is_numeric(value: str) -> bool:
    """
    Check if a value is numeric, including strings with scientific notation.
    """
    return bool(re.match(r"^-?\d+(\.\d+)?([eE]-?\d+)?$", value))


def range_validator(num: int, lower_bound: int, upper_bound: int) -> bool:
    return (num >= lower_bound) and (num <= upper_bound)


def format_number(n, precision=4) -> str:
    if isinstance(n, float) and n.is_integer():
        return str(int(n))
    if isinstance(n, int):
        return str(n)
    return f"{n:.{precision}g}"


def guild_only(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Find the interaction argument
        interaction = None
        for arg in args:
            if isinstance(arg, discord.Interaction):
                interaction = arg
                break
        if interaction and interaction.guild is None:
            await interaction.response.send_message("This command is only available in servers.", ephemeral=True)
            return
        return await func(*args, **kwargs)
    return wrapper
