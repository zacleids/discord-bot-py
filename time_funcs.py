from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from pytz import all_timezones

from errors import InvalidInputError
from models import WorldClock

all_timezones_lower = list(map(str.lower, all_timezones))

DB_NAME = "db/bot.db"


def get_timezone(guild_id: int, timezone_str: str) -> WorldClock:
    try:
        return WorldClock.get(WorldClock.guild_id == guild_id, WorldClock.timezone_str == timezone_str)
    except WorldClock.DoesNotExist:
        return None


def add_timezone(guild_id: int, timezone_str: str, label=None) -> str:
    if WorldClock.select().where(WorldClock.guild_id == guild_id, WorldClock.timezone_str == timezone_str).exists():
        return f"Timezone already exists: {timezone_str}"
    WorldClock.create(guild_id=guild_id, timezone_str=timezone_str, label=label)
    return f"Timezone added: {timezone_str}{' with label ' + label if label else ''}"


def remove_timezone(guild_id: int, timezone_str: str) -> str:
    query = WorldClock.delete().where(WorldClock.guild_id == guild_id, WorldClock.timezone_str == timezone_str)
    if query.execute():
        return f"Timezone {timezone_str} removed"
    return "Timezone not found."


def update_timezone(guild_id: int, timezone_str: str, label=None):
    WorldClock.update(label=label).where(WorldClock.guild_id == guild_id, WorldClock.timezone_str == timezone_str).execute()


def list_timezones(guild_id: int) -> list[WorldClock]:
    return WorldClock.select().where(WorldClock.guild_id == guild_id).order_by(WorldClock.created_at.asc())


def format_time(dt: datetime) -> str:
    # will format to Saturday February 15 12:22 AM
    return dt.strftime("%A %B %d %I:%M %p")


def format_tzs_response_str(tzs: list[WorldClock]) -> str:
    result = ""

    for tz in tzs:
        result += tz.format() + "\n"

    return result


def handle_world_clock_command(args: list[str], guild_id: int):
    result = None
    if not args:
        result = "Please provide a subcommand (add, remove, list)."
    else:
        subcommand = args[0].lower()
        sub_args = args[1:]

        match subcommand:
            case "add":
                if not sub_args:
                    result = "Please provide a timezone to add."
                else:
                    tz = get_valid_timezone(" ".join(sub_args))
                    result = add_timezone(guild_id, tz)
            case "remove":
                if not sub_args:
                    result = "Please provide the timezone to remove."
                else:
                    tz = get_valid_timezone(" ".join(sub_args))
                    result = remove_timezone(guild_id, tz)

            case "list":
                tzs = list_timezones(guild_id)
                if tzs:
                    result = format_tzs_response_str(tzs)
                else:
                    result = "No timezones added to world clock"
            case _:
                result = f"Invalid subcommand {subcommand}. Please provide a subcommand (add, remove, list)."
    return result


def return_all_timezones():
    return all_timezones + list(map(str.lower, all_timezones))


def get_valid_timezone(zone: str) -> str:
    if zone in all_timezones:
        return zone
    elif zone in all_timezones_lower:
        return all_timezones[all_timezones_lower.index(zone)]
    else:
        raise InvalidInputError("Timezone not found")


class EditTimezoneLabelModal(discord.ui.Modal, title="Edit Timezone Label"):
    def __init__(self, guild_id: int, timezone_str: str, existing_label: str):
        super().__init__()
        self.guild_id = guild_id
        self.timezone_str = timezone_str

        # Prefill the text field with the existing task
        self.task_input = discord.ui.TextInput(label="Edit label", default=existing_label, style=discord.TextStyle.short)
        self.add_item(self.task_input)

    async def on_submit(self, interaction: discord.Interaction):
        new_label = self.task_input.value
        update_timezone(self.guild_id, self.timezone_str, new_label)
        await interaction.response.send_message("Label updated successfully!")


def format(wc: WorldClock) -> str:
    label = wc.label + " | " if wc.label else ""
    zone = wc.timezone_str
    return f"{label}{zone}: **{format_time(datetime.now(ZoneInfo(zone)))}**"


WorldClock.format = format
