from datetime import datetime, timezone

import discord
from discord import Client

from . import time_funcs
from .log import get_ray_id, log_event
from .models import LiveMessage

SUPERSEDED_BY_NEW_MESSAGE_REASON = "superseded_by_new_message"
LIVE_MESSAGE_REFRESH_INTERVAL_SECONDS = 60
LIVE_MESSAGE_REFRESH_SLOT_SECONDS = 10


def stop_live_message(live_message: LiveMessage, stop_reason: str, *, level: str = "info"):
    stopped_at = datetime.now(timezone.utc).replace(tzinfo=None)
    LiveMessage.update(stopped_at=stopped_at, stop_reason=stop_reason).where(LiveMessage.id == live_message.id).execute()
    log_event(
        "LIVE_MESSAGE_STOPPED",
        {
            "ray_id": get_ray_id(),
            "event": "LIVE_MESSAGE_STOPPED",
            "live_message_id": live_message.id,
            "message_type": live_message.message_type,
            "message_id": live_message.message_id,
            "channel_id": live_message.channel_id,
            "guild_id": live_message.guild_id,
            "user_id": live_message.user_id,
            "stop_reason": stop_reason,
            "stopped_at": str(stopped_at),
        },
        level=level,
    )


async def _get_live_message_channel(client: Client, channel_id: int):
    channel = client.get_channel(channel_id)
    if channel is not None:
        return channel
    return await client.fetch_channel(channel_id)


async def _refresh_world_clock_live_message(client: Client, live_message: LiveMessage, now: datetime):
    scope_user_id = None if live_message.guild_id is not None else live_message.user_id
    embed = time_funcs.build_world_clock_embed(
        live_message.guild_id,
        scope_user_id,
        now=now,
        expires_at=live_message.expires_at,
    )
    channel = await _get_live_message_channel(client, live_message.channel_id)
    message = await channel.fetch_message(live_message.message_id)
    await message.edit(embed=embed)
    LiveMessage.update(last_refreshed_at=now.replace(tzinfo=None)).where(LiveMessage.id == live_message.id).execute()
    log_event(
        "LIVE_MESSAGE_REFRESHED",
        {
            "ray_id": get_ray_id(),
            "event": "LIVE_MESSAGE_REFRESHED",
            "live_message_id": live_message.id,
            "message_type": live_message.message_type,
            "message_id": live_message.message_id,
            "channel_id": live_message.channel_id,
            "guild_id": live_message.guild_id,
            "user_id": live_message.user_id,
        },
        level="debug",
    )


async def _mark_world_clock_live_message_superseded(client: Client, live_message: LiveMessage, now: datetime):
    scope_user_id = None if live_message.guild_id is not None else live_message.user_id
    embed = time_funcs.build_world_clock_embed(
        live_message.guild_id,
        scope_user_id,
        now=now,
        expires_at=live_message.expires_at,
        live_status_text=time_funcs.WORLD_CLOCK_SUPERSEDED_STATUS,
    )
    channel = await _get_live_message_channel(client, live_message.channel_id)
    message = await channel.fetch_message(live_message.message_id)
    await message.edit(embed=embed)


def _live_message_scope_filter(guild_id: int | None, user_id: int) -> object:
    if guild_id is None:
        return LiveMessage.guild_id.is_null() & (LiveMessage.user_id == user_id)
    return LiveMessage.guild_id == guild_id


def _live_message_expiry_kind_filter(expires_at: datetime | None) -> object:
    return LiveMessage.expires_at.is_null() if expires_at is None else LiveMessage.expires_at.is_null(False)


def find_conflicting_live_messages(
    message_type: str,
    guild_id: int | None,
    user_id: int,
    expires_at: datetime | None,
    *,
    exclude_id: int | None = None,
) -> list[LiveMessage]:
    query = (
        LiveMessage.select()
        .where(
            LiveMessage.message_type == message_type,
            LiveMessage.stopped_at.is_null(),
            _live_message_scope_filter(guild_id, user_id),
            _live_message_expiry_kind_filter(expires_at),
        )
        .order_by(LiveMessage.created_at.asc(), LiveMessage.id.asc())
    )
    if exclude_id is not None:
        query = query.where(LiveMessage.id != exclude_id)
    return list(query)


async def supersede_live_message(client: Client, live_message: LiveMessage, now: datetime):
    try:
        if live_message.message_type == time_funcs.LIVE_MESSAGE_TYPE_WORLD_CLOCK:
            await _mark_world_clock_live_message_superseded(client, live_message, now)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException) as exc:
        log_event(
            "LIVE_MESSAGE_SUPERSEDE_UPDATE_ERROR",
            {
                "ray_id": get_ray_id(),
                "event": "LIVE_MESSAGE_SUPERSEDE_UPDATE_ERROR",
                "live_message_id": live_message.id,
                "message_type": live_message.message_type,
                "message_id": live_message.message_id,
                "channel_id": live_message.channel_id,
                "guild_id": live_message.guild_id,
                "user_id": live_message.user_id,
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
            level="warning",
        )
    finally:
        stop_live_message(live_message, SUPERSEDED_BY_NEW_MESSAGE_REASON)


async def supersede_conflicting_live_messages(client: Client, live_message: LiveMessage, now: datetime):
    conflicts = find_conflicting_live_messages(
        live_message.message_type,
        live_message.guild_id,
        live_message.user_id,
        live_message.expires_at,
        exclude_id=live_message.id,
    )
    for conflict in conflicts:
        await supersede_live_message(client, conflict, now)
    return conflicts


def should_refresh_live_message_this_tick(
    live_message: LiveMessage,
    now: datetime,
    *,
    refresh_interval_seconds: int = LIVE_MESSAGE_REFRESH_INTERVAL_SECONDS,
    slot_seconds: int = LIVE_MESSAGE_REFRESH_SLOT_SECONDS,
) -> bool:
    slot_count = max(1, refresh_interval_seconds // slot_seconds)
    current_slot = int(now.timestamp()) // slot_seconds % slot_count
    message_slot = live_message.id % slot_count
    return message_slot == current_slot


LIVE_MESSAGE_REFRESH_HANDLERS = {
    time_funcs.LIVE_MESSAGE_TYPE_WORLD_CLOCK: _refresh_world_clock_live_message,
}


async def refresh_live_message(client: Client, live_message: LiveMessage, now: datetime):
    refresh_handler = LIVE_MESSAGE_REFRESH_HANDLERS.get(live_message.message_type)
    if refresh_handler is None:
        stop_live_message(live_message, "unsupported_message_type", level="warning")
        return
    await refresh_handler(client, live_message, now)
