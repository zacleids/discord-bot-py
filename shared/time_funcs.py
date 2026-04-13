from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import discord

from .errors import InvalidInputError
from .log import get_ray_id, log_event, ray_id_var
from .models import WorldClock
from .timezone import get_valid_timezone

LIVE_MESSAGE_TYPE_WORLD_CLOCK = "world_clock_list_v1"
LIVE_MESSAGE_EXPIRY = timedelta(hours=24)
DB_NAME = "db/bot.db"


def _validate_scope(guild_id: int | None, user_id: int | None):
    if guild_id is None and user_id is None:
        raise InvalidInputError("World clock scope requires either guild_id or user_id")
    if guild_id is not None and user_id is not None:
        raise InvalidInputError("World clock scope cannot include both guild_id and user_id")


def _scope_filter(guild_id: int | None, user_id: int | None):
    _validate_scope(guild_id, user_id)
    if guild_id is None:
        return (WorldClock.guild_id.is_null()) & (WorldClock.user_id == user_id)
    return (WorldClock.guild_id == guild_id) & WorldClock.user_id.is_null()


def get_timezone(guild_id: int | None, user_id: int | None, timezone_str: str) -> WorldClock:
    try:
        return WorldClock.get(_scope_filter(guild_id, user_id), WorldClock.timezone_str == timezone_str)
    except WorldClock.DoesNotExist:
        return None


def add_timezone(guild_id: int | None, user_id: int | None, timezone_str: str, label=None) -> str:
    if WorldClock.select().where(_scope_filter(guild_id, user_id), WorldClock.timezone_str == timezone_str).exists():
        return f"Timezone already exists: {timezone_str}"
    WorldClock.create(guild_id=guild_id, user_id=user_id if guild_id is None else None, timezone_str=timezone_str, label=label)
    return f"Timezone added: {timezone_str}{' with label ' + label if label else ''}"


def remove_timezone(guild_id: int | None, user_id: int | None, timezone_str: str) -> str:
    query = WorldClock.delete().where(_scope_filter(guild_id, user_id), WorldClock.timezone_str == timezone_str)
    if query.execute():
        return f"Timezone {timezone_str} removed"
    return "Timezone not found."


def update_timezone(guild_id: int | None, user_id: int | None, timezone_str: str, label=None):
    WorldClock.update(label=label).where(_scope_filter(guild_id, user_id), WorldClock.timezone_str == timezone_str).execute()


def list_timezones(guild_id: int | None, user_id: int | None = None) -> list[WorldClock]:
    return WorldClock.select().where(_scope_filter(guild_id, user_id)).order_by(WorldClock.created_at.asc())


def _get_reference_now(now: datetime | None = None) -> datetime:
    reference_now = now or datetime.now(timezone.utc)
    if reference_now.tzinfo is None:
        return reference_now.replace(tzinfo=timezone.utc)
    return reference_now.astimezone(timezone.utc)


def get_live_message_expiry(now: datetime | None = None) -> datetime:
    return (_get_reference_now(now) + LIVE_MESSAGE_EXPIRY).replace(tzinfo=None)


def get_world_clock_local_time(world_clock: WorldClock, now: datetime | None = None) -> datetime:
    return _get_reference_now(now).astimezone(ZoneInfo(world_clock.timezone_str))


def sort_world_clocks_by_display_time(tzs: list[WorldClock], now: datetime | None = None) -> list[WorldClock]:
    reference_now = _get_reference_now(now)
    return sorted(
        tzs,
        key=lambda tz: (
            get_world_clock_local_time(tz, reference_now).replace(tzinfo=None),
            tz.label or "",
            tz.timezone_str,
        ),
    )


def format_time(dt: datetime) -> str:
    # will format to Saturday February 15 12:22 AM
    return dt.strftime("%A %B %d %I:%M %p")


def format_tzs_response_str(tzs: list[WorldClock], now: datetime | None = None) -> str:
    result = ""

    for tz in sort_world_clocks_by_display_time(tzs, now=now):
        result += tz.format(now=now) + "\n"

    return result


def _get_world_clock_display_lines(tzs: list[WorldClock], now: datetime | None = None) -> list[str]:
    lines = []
    for tz in sort_world_clocks_by_display_time(tzs, now=now):
        local_time = get_world_clock_local_time(tz, now)
        formatted_time = format_time(local_time)
        if tz.label:
            line = f"**{tz.label}** | {tz.timezone_str} | {formatted_time}"
        else:
            line = f"**{tz.timezone_str}** | {formatted_time}"
        lines.append(line)
    return lines


def build_world_clock_embed(
    guild_id: int | None,
    user_id: int | None,
    *,
    now: datetime | None = None,
    expires_at: datetime | None = None,
) -> discord.Embed:
    reference_now = _get_reference_now(now)
    tzs = list_timezones(guild_id, user_id)
    embed = discord.Embed(title="World Clock", color=discord.Color.blue())

    if tzs:
        embed.description = "\n".join(_get_world_clock_display_lines(tzs, now=reference_now))
    else:
        embed.description = "There are no clocks in your world clock"

    scope_label = "DM" if guild_id is None else "Guild"
    status_lines = [
        f"Updated: {discord.utils.format_dt(reference_now, style='R')}",
    ]
    if expires_at is not None:
        expiry_time = _get_reference_now(expires_at)
        relative_expiry = discord.utils.format_dt(expiry_time, style="R")
        # absolute_expiry = discord.utils.format_dt(expiry_time, style='F')
        # status_lines.append(f"Expires: {relative_expiry} ({absolute_expiry})")
        status_lines.append(f"Expires: {relative_expiry}")
    embed.add_field(name="Live Status", value=" | ".join(status_lines), inline=False)
    embed.set_footer(text=f"{scope_label} scope | Updates every minute")
    return embed


def handle_world_clock_command(args: list[str], guild_id: int | None, user_id: int | None = None):
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
                    result = add_timezone(guild_id, user_id, tz)
            case "remove":
                if not sub_args:
                    result = "Please provide the timezone to remove."
                else:
                    tz = get_valid_timezone(" ".join(sub_args))
                    result = remove_timezone(guild_id, user_id, tz)

            case "list":
                tzs = list_timezones(guild_id, user_id)
                if tzs:
                    result = format_tzs_response_str(tzs)
                else:
                    result = "No timezones added to world clock"
            case _:
                result = f"Invalid subcommand {subcommand}. Please provide a subcommand (add, remove, list)."
    return result


class EditTimezoneLabelModal(discord.ui.Modal, title="Edit Timezone Label"):
    def __init__(self, guild_id: int | None, user_id: int | None, timezone_str: str, existing_label: str):
        super().__init__()
        self.guild_id = guild_id
        self.user_id = user_id
        self.timezone_str = timezone_str
        self.existing_label = existing_label
        self.ray_id = get_ray_id()

        # Prefill the text field with the existing task
        self.task_input = discord.ui.TextInput(label="Edit label", default=existing_label, style=discord.TextStyle.short)
        self.add_item(self.task_input)

    async def on_submit(self, interaction: discord.Interaction):
        token = ray_id_var.set(self.ray_id)
        try:
            new_label = self.task_input.value
            log_event(
                "AUDIT_LOG",
                {
                    "event": "AUDIT_LOG",
                    "action": "clock_edit",
                    "user_id": interaction.user.id,
                    "guild_id": self.guild_id,
                    "timezone_str": self.timezone_str,
                    "before": {"label": self.existing_label},
                    "after": {"label": new_label},
                    "ray_id": get_ray_id(),
                },
                level="info",
            )
            update_timezone(self.guild_id, self.user_id, self.timezone_str, new_label)
            await interaction.response.send_message("Label updated successfully!")
        finally:
            ray_id_var.reset(token)


def format(wc: WorldClock, now: datetime | None = None) -> str:
    label = wc.label + " | " if wc.label else ""
    zone = wc.timezone_str
    return f"{label}{zone}: **{format_time(get_world_clock_local_time(wc, now))}**"


WorldClock.format = format
