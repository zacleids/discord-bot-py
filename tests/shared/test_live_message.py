from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from db_test_utils import wipe_table

from shared import live_messages, time_funcs
from shared.models import LiveMessage, WorldClock


@pytest.fixture(autouse=True)
def clear_live_message_table():
    wipe_table(LiveMessage)
    wipe_table(WorldClock)


def test_live_message_persists_guild_scope_and_expiry():
    expires_at = datetime(2030, 1, 1, 0, 0, 0)

    live_message = LiveMessage.create(
        message_type="world_clock_list_v1",
        message_id=123456789,
        channel_id=987654321,
        guild_id=555,
        user_id=111,
        expires_at=expires_at,
    )

    loaded = LiveMessage.get_by_id(live_message.id)

    assert loaded.message_type == "world_clock_list_v1"
    assert loaded.message_id == 123456789
    assert loaded.channel_id == 987654321
    assert loaded.guild_id == 555
    assert loaded.user_id == 111
    assert loaded.expires_at == expires_at
    assert loaded.stopped_at is None
    assert loaded.stop_reason is None


def test_live_message_supports_dm_scope():
    live_message = LiveMessage.create(
        message_type="world_clock_list_v1",
        message_id=222333444,
        channel_id=444333222,
        guild_id=None,
        user_id=222,
        expires_at=datetime(2030, 1, 2, 0, 0, 0),
    )

    loaded = LiveMessage.get_by_id(live_message.id)

    assert loaded.guild_id is None
    assert loaded.user_id == 222
    assert loaded.stopped_at is None
    assert loaded.stop_reason is None


def test_live_message_supports_nullable_expiry():
    live_message = LiveMessage.create(
        message_type="world_clock_list_v1",
        message_id=999888777,
        channel_id=777888999,
        guild_id=333,
        user_id=444,
        expires_at=None,
    )

    loaded = LiveMessage.get_by_id(live_message.id)

    assert loaded.guild_id == 333
    assert loaded.user_id == 444
    assert loaded.expires_at is None
    assert loaded.stopped_at is None
    assert loaded.stop_reason is None


def test_find_conflicting_live_messages_matches_scope_and_expiry_kind():
    finite_live_message = LiveMessage.create(
        message_type=time_funcs.LIVE_MESSAGE_TYPE_WORLD_CLOCK,
        message_id=1001,
        channel_id=2001,
        guild_id=555,
        user_id=111,
        expires_at=datetime(2030, 1, 1, 0, 0, 0),
    )
    LiveMessage.create(
        message_type=time_funcs.LIVE_MESSAGE_TYPE_WORLD_CLOCK,
        message_id=1002,
        channel_id=2002,
        guild_id=555,
        user_id=222,
        expires_at=datetime(2030, 1, 2, 0, 0, 0),
    )
    LiveMessage.create(
        message_type=time_funcs.LIVE_MESSAGE_TYPE_WORLD_CLOCK,
        message_id=1003,
        channel_id=2003,
        guild_id=555,
        user_id=333,
        expires_at=None,
    )
    stopped_message = LiveMessage.create(
        message_type=time_funcs.LIVE_MESSAGE_TYPE_WORLD_CLOCK,
        message_id=1004,
        channel_id=2004,
        guild_id=555,
        user_id=444,
        expires_at=datetime(2030, 1, 3, 0, 0, 0),
    )
    (
        LiveMessage.update(stopped_at=datetime(2029, 1, 1, 0, 0, 0), stop_reason="expired")
        .where(LiveMessage.id == stopped_message.id)
        .execute()
    )
    LiveMessage.create(
        message_type=time_funcs.LIVE_MESSAGE_TYPE_WORLD_CLOCK,
        message_id=1005,
        channel_id=2005,
        guild_id=999,
        user_id=555,
        expires_at=datetime(2030, 1, 4, 0, 0, 0),
    )

    conflicts = live_messages.find_conflicting_live_messages(
        time_funcs.LIVE_MESSAGE_TYPE_WORLD_CLOCK,
        555,
        111,
        finite_live_message.expires_at,
        exclude_id=finite_live_message.id,
    )

    assert [message.message_id for message in conflicts] == [1002]


@pytest.mark.asyncio
async def test_supersede_live_message_updates_embed_and_reason(monkeypatch):
    live_message = LiveMessage.create(
        message_type=time_funcs.LIVE_MESSAGE_TYPE_WORLD_CLOCK,
        message_id=123456,
        channel_id=654321,
        guild_id=555,
        user_id=111,
        expires_at=datetime(2030, 1, 1, 0, 0, 0),
    )
    mock_message = AsyncMock()
    mock_channel = AsyncMock()
    mock_channel.fetch_message.return_value = mock_message

    async def fake_get_live_message_channel(client, channel_id):
        assert channel_id == 654321
        return mock_channel

    monkeypatch.setattr(live_messages, "_get_live_message_channel", fake_get_live_message_channel)

    await live_messages.supersede_live_message(AsyncMock(), live_message, datetime(2024, 2, 15, 12, 0, tzinfo=timezone.utc))

    loaded = LiveMessage.get_by_id(live_message.id)

    mock_message.edit.assert_called_once()
    edited_embed = mock_message.edit.await_args.kwargs["embed"]
    assert edited_embed.fields[0].value == time_funcs.WORLD_CLOCK_SUPERSEDED_STATUS
    assert loaded.stop_reason == live_messages.SUPERSEDED_BY_NEW_MESSAGE_REASON
    assert loaded.stopped_at is not None


def test_should_refresh_live_message_this_tick_uses_staggered_slots():
    live_message = LiveMessage.create(
        message_type=time_funcs.LIVE_MESSAGE_TYPE_WORLD_CLOCK,
        message_id=2001,
        channel_id=3001,
        guild_id=555,
        user_id=111,
        expires_at=datetime(2030, 1, 1, 0, 0, 0),
    )
    slot_count = live_messages.LIVE_MESSAGE_REFRESH_INTERVAL_SECONDS // live_messages.LIVE_MESSAGE_REFRESH_SLOT_SECONDS
    matching_slot = live_message.id % slot_count
    matching_epoch_seconds = matching_slot * live_messages.LIVE_MESSAGE_REFRESH_SLOT_SECONDS
    non_matching_epoch_seconds = ((matching_slot + 1) % slot_count) * live_messages.LIVE_MESSAGE_REFRESH_SLOT_SECONDS

    matching_now = datetime.fromtimestamp(matching_epoch_seconds, tz=timezone.utc)
    non_matching_now = datetime.fromtimestamp(non_matching_epoch_seconds, tz=timezone.utc)

    assert live_messages.should_refresh_live_message_this_tick(live_message, matching_now)
    assert not live_messages.should_refresh_live_message_this_tick(live_message, non_matching_now)
