from datetime import datetime, timezone

from discord import Client

from . import time_funcs
from .log import get_ray_id, log_event
from .models import LiveMessage


def stop_live_message(live_message: LiveMessage, reason: str, *, level: str = "info"):
    stopped_at = datetime.now(timezone.utc).replace(tzinfo=None)
    LiveMessage.update(stopped_at=stopped_at, stop_reason=reason).where(LiveMessage.id == live_message.id).execute()
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
            "reason": reason,
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


LIVE_MESSAGE_REFRESH_HANDLERS = {
    time_funcs.LIVE_MESSAGE_TYPE_WORLD_CLOCK: _refresh_world_clock_live_message,
}


async def refresh_live_message(client: Client, live_message: LiveMessage, now: datetime):
    refresh_handler = LIVE_MESSAGE_REFRESH_HANDLERS.get(live_message.message_type)
    if refresh_handler is None:
        stop_live_message(live_message, "unsupported_message_type", level="warning")
        return
    await refresh_handler(client, live_message, now)
