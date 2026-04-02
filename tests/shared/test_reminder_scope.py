from datetime import datetime

import pytest
from db_test_utils import wipe_table

from shared.models import Reminder

USER_ID = 100
GUILD_ID = 200
CHANNEL_ID = 300


@pytest.fixture(autouse=True)
def clear_reminder_table():
    wipe_table(Reminder)


def test_private_reminder_uses_null_guild_scope():
    reminder = Reminder.create(
        user_id=USER_ID,
        guild_id=None,
        channel_id=CHANNEL_ID,
        message="Private reminder",
        remind_at=datetime(2030, 1, 1, 0, 0, 0),
        is_private=True,
    )
    loaded = Reminder.get_by_id(reminder.id)
    assert loaded.guild_id is None
    assert loaded.is_private is True


def test_public_reminder_keeps_guild_scope():
    reminder = Reminder.create(
        user_id=USER_ID,
        guild_id=GUILD_ID,
        channel_id=CHANNEL_ID,
        message="Public reminder",
        remind_at=datetime(2030, 1, 1, 0, 0, 0),
        is_private=False,
    )
    loaded = Reminder.get_by_id(reminder.id)
    assert loaded.guild_id == GUILD_ID
    assert loaded.is_private is False
