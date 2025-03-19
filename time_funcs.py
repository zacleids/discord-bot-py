import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from pytz import timezone, all_timezones

from errors import InvalidInputError

all_timezones_lower = list(map(str.lower, all_timezones))

DB_NAME = "db/bot.db"


def create_db():
    """Create the database and the tasks table if they don't exist."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS world_clock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            timezone_str TEXT NOT NULL,
            label TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    connection.commit()
    connection.close()


def get_timezone(guild_id: int, timezone_str: str) -> tuple[int, str, str]:
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("SELECT guild_id, timezone_str, label FROM world_clock WHERE guild_id = ? AND timezone_str = ?", (guild_id, timezone_str))
    tz = cursor.fetchone()

    connection.close()
    return tz if tz else None


def add_timezone(guild_id: int, timezone_str: str, label=None) -> str:
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # Check if timezone_entry exists
    cursor.execute("SELECT id FROM world_clock WHERE guild_id = ? AND timezone_str = ?", (guild_id, timezone_str))
    timezone_entry = cursor.fetchone()
    if timezone_entry:
        connection.close()
        return f"Timezone already exists: {timezone_str}"

    # Insert the new task at the specified position
    cursor.execute("INSERT INTO world_clock (guild_id, timezone_str, label) VALUES (?, ?, ?)", (guild_id, timezone_str, label))

    connection.commit()
    connection.close()

    return f"Timezone added: {timezone_str}{' with label ' + label if label else ''}"


def remove_timezone(guild_id: int, timezone_str: str) -> str:
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # Check if timezone_entry exists
    cursor.execute("SELECT id, timezone_str, label FROM world_clock WHERE guild_id = ? AND timezone_str = ?", (guild_id, timezone_str))
    timezone_entry = cursor.fetchone()
    if not timezone_entry:
        connection.close()
        return "Timezone not found."

    timezone_id = timezone_entry[0]

    # Delete the timezone_entry
    cursor.execute("DELETE FROM world_clock WHERE id = ?", (timezone_id,))

    connection.commit()
    connection.close()

    return f"Timezone {timezone_entry[1]} removed"


def update_timezone(guild_id: int, timezone_str: str, label=None):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("UPDATE world_clock SET label = ? WHERE guild_id = ? AND timezone_str = ?", (label, guild_id, timezone_str))
    connection.commit()
    connection.close()


def list_timezones(guild_id: int):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("""
            SELECT label, timezone_str
            FROM world_clock
            WHERE guild_id = ?
            ORDER BY created_at ASC
        """, (guild_id,))

    tzs = cursor.fetchall()
    connection.close()

    return tzs


def format_time(dt: datetime) -> str:
    # will format to Saturday February 15 12:22 AM
    return dt.strftime("%A %B %d %I:%M %p")


def format_tzs_response_str(tzs) -> str:
    result = ""

    for tz in tzs:
        label = tz[0] + " | " if tz[0] else ""
        zone = tz[1]
        result = result + f"{label}{zone}: **{format_time(datetime.now(ZoneInfo(zone)))}**\n"

    return result


def handle_world_clock_command(args: list[str], guild_id: int):
    result = None
    if not args:
        result = "Please provide a subcommand (add, remove, list)."
    else:
        subcommand = args[0]
        sub_args = args[1:]

        match subcommand:
            case "add":
                if not sub_args:
                    result = "Please provide a task to add."
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
        self.task_input = discord.ui.TextInput(
            label="Edit label",
            default=existing_label,
            style=discord.TextStyle.short
        )
        self.add_item(self.task_input)

    async def on_submit(self, interaction: discord.Interaction):
        new_label = self.task_input.value
        update_timezone(self.guild_id, self.timezone_str, new_label)
        await interaction.response.send_message(f"Label updated successfully!")
