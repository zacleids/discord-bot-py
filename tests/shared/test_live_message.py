from datetime import datetime

import pytest
from db_test_utils import wipe_table

from shared.models import LiveMessage


@pytest.fixture(autouse=True)
def clear_live_message_table():
    wipe_table(LiveMessage)


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
