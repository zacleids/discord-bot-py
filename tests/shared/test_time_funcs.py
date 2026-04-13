from datetime import datetime, timezone

import pytest

from shared.time_funcs import (
    InvalidInputError,
    WorldClock,
    add_timezone,
    build_world_clock_embed,
    format_time,
    format_tzs_response_str,
    get_live_message_expiry,
    get_valid_timezone,
    get_world_clock_local_time,
    list_timezones,
    remove_timezone,
    sort_world_clocks_by_display_time,
    update_timezone,
)


@pytest.fixture(autouse=True)
def setup_function():
    # Clear WorldClock table before each test
    WorldClock.delete().execute()


GUILD_ID = 1
USER_ID = 42


def test_add_timezone():
    guild_id = GUILD_ID
    tz = "America/Denver"
    msg = add_timezone(guild_id, None, tz)
    assert "added" in msg.lower()
    # Should be in the list
    tzs = list_timezones(guild_id, None)
    assert any(t.timezone_str == tz for t in tzs)


def test_remove_timezone():
    guild_id = GUILD_ID
    tz = "America/Chicago"
    add_timezone(guild_id, None, tz)
    msg = remove_timezone(guild_id, None, tz)
    assert "removed" in msg.lower()
    # Should not be in the list
    tzs = list_timezones(guild_id, None)
    assert all(t.timezone_str != tz for t in tzs)


def test_update_timezone_label():
    guild_id = GUILD_ID
    tz = "America/New_York"
    add_timezone(guild_id, None, tz)
    update_timezone(guild_id, None, tz, label="NYC")
    tzs = list_timezones(guild_id, None)
    assert tzs[0].label == "NYC"


def test_list_timezones():
    guild_id = GUILD_ID
    tz1 = "America/Los_Angeles"
    tz2 = "Europe/London"
    add_timezone(guild_id, None, tz1)
    add_timezone(guild_id, None, tz2)
    tzs = list_timezones(guild_id, None)
    assert len(tzs) == 2
    assert {t.timezone_str for t in tzs} == {tz1, tz2}


def test_get_valid_timezone():
    # Should return canonical name for lower case
    tz = get_valid_timezone("america/los_angeles")
    assert tz == "America/Los_Angeles"
    # Should return as-is for canonical
    tz2 = get_valid_timezone("Europe/London")
    assert tz2 == "Europe/London"


def test_add_duplicate_timezone():
    guild_id = GUILD_ID
    tz = "America/Los_Angeles"
    msg1 = add_timezone(guild_id, None, tz)
    msg2 = add_timezone(guild_id, None, tz)
    assert "added" in msg1.lower()
    assert "already exists" in msg2.lower()


def test_remove_nonexistent_timezone():
    guild_id = GUILD_ID
    tz = "America/New_York"
    msg = remove_timezone(guild_id, None, tz)
    assert "not found" in msg.lower()


def test_case_insensitive_timezone_add_remove():
    guild_id = GUILD_ID
    tz = "America/Los_Angeles"
    tz_lower = "america/los_angeles"
    msg1 = add_timezone(guild_id, None, tz)
    assert "added" in msg1.lower()
    # Remove using lower case
    tz_valid = get_valid_timezone(tz_lower)
    msg2 = remove_timezone(guild_id, None, tz_valid)
    assert "removed" in msg2.lower()


def test_invalid_timezone():
    with pytest.raises(InvalidInputError):
        get_valid_timezone("fake/timezone")


def test_list_timezones_empty():
    guild_id = GUILD_ID
    tzs = list_timezones(guild_id, None)
    assert tzs == []


def test_update_label_nonexistent_timezone():
    guild_id = GUILD_ID
    tz = "America/Chicago"
    # Should not throw
    update_timezone(guild_id, None, tz, label="Central")
    # Should still not exist
    assert list_timezones(guild_id, None) == []


def test_add_timezone_with_label_response():
    guild_id = GUILD_ID
    tz = "Asia/Tokyo"
    label = "Japan Time"
    msg = add_timezone(guild_id, None, tz, label=label)
    assert "added" in msg.lower()
    assert f"with label {label}" in msg


def test_get_valid_timezone_canonical():
    tz = get_valid_timezone("Europe/London")
    assert tz == "Europe/London"


def test_get_valid_timezone_lowercase():
    tz = get_valid_timezone("europe/london")
    assert tz == "Europe/London"


def test_worldclock_format():
    # Create a WorldClock instance (not saved to DB)
    wc = WorldClock(guild_id=GUILD_ID, user_id=None, timezone_str="Asia/Tokyo", label="Japan Time")
    formatted = wc.format()
    # Should include the label and timezone
    assert "Japan Time" in formatted
    assert "Asia/Tokyo" in formatted


def test_format_time_output_variants():
    from datetime import datetime

    dt = datetime(2024, 2, 15, 0, 22)  # Thursday February 15 12:22 AM
    formatted = format_time(dt)
    assert formatted == "Thursday February 15 12:22 AM"
    dt2 = datetime(2024, 12, 25, 18, 5)  # Wednesday December 25 06:05 PM
    formatted2 = format_time(dt2)
    assert formatted2 == "Wednesday December 25 06:05 PM"


def test_format_tzs_response_str():
    # Create a list of WorldClock objects
    tzs = [
        WorldClock(guild_id=GUILD_ID, user_id=None, timezone_str="Asia/Tokyo", label="Japan Time"),
        WorldClock(guild_id=GUILD_ID, user_id=None, timezone_str="Europe/London", label="London"),
        WorldClock(guild_id=GUILD_ID, user_id=None, timezone_str="US/Pacific", label="PST"),
    ]
    # Assume format_tzs_response_str returns a string listing all timezones
    response = format_tzs_response_str(tzs)
    assert "Japan Time" in response
    assert "Asia/Tokyo" in response
    assert "London" in response
    assert "Europe/London" in response
    assert "PST" in response
    assert "US/Pacific" in response


def test_private_worldclock_isolated_from_guild_scope():
    tz = "Asia/Tokyo"
    add_timezone(None, USER_ID, tz)
    assert any(t.timezone_str == tz for t in list_timezones(None, USER_ID))
    assert all(t.timezone_str != tz for t in list_timezones(GUILD_ID, None))


def test_worldclock_scope_requires_exactly_one_owner_dimension():
    with pytest.raises(InvalidInputError):
        list_timezones(None, None)

    with pytest.raises(InvalidInputError):
        list_timezones(GUILD_ID, USER_ID)


def test_sort_world_clocks_by_display_time_orders_by_local_wall_time():
    reference_now = datetime(2024, 2, 15, 12, 0, tzinfo=timezone.utc)
    tzs = [
        WorldClock(guild_id=GUILD_ID, user_id=None, timezone_str="Asia/Tokyo", label="Tokyo"),
        WorldClock(guild_id=GUILD_ID, user_id=None, timezone_str="Europe/London", label="London"),
        WorldClock(guild_id=GUILD_ID, user_id=None, timezone_str="America/Los_Angeles", label="Los Angeles"),
    ]

    sorted_tzs = sort_world_clocks_by_display_time(tzs, now=reference_now)

    assert [tz.timezone_str for tz in sorted_tzs] == [
        "America/Los_Angeles",
        "Europe/London",
        "Asia/Tokyo",
    ]


def test_format_tzs_response_str_uses_sorted_display_order():
    reference_now = datetime(2024, 2, 15, 12, 0, tzinfo=timezone.utc)
    tzs = [
        WorldClock(guild_id=GUILD_ID, user_id=None, timezone_str="Asia/Tokyo", label="Tokyo"),
        WorldClock(guild_id=GUILD_ID, user_id=None, timezone_str="Europe/London", label="London"),
        WorldClock(guild_id=GUILD_ID, user_id=None, timezone_str="America/Los_Angeles", label="Los Angeles"),
    ]

    response = format_tzs_response_str(tzs, now=reference_now)

    assert response.index("Los Angeles") < response.index("London")
    assert response.index("London") < response.index("Tokyo")


def test_build_world_clock_embed_for_dm_scope_uses_sorted_lines_and_expiry():
    reference_now = datetime(2024, 2, 15, 12, 0, tzinfo=timezone.utc)
    add_timezone(None, USER_ID, "Asia/Tokyo", label="Tokyo")
    add_timezone(None, USER_ID, "America/Los_Angeles", label="Los Angeles")

    embed = build_world_clock_embed(None, USER_ID, now=reference_now, expires_at=get_live_message_expiry(reference_now))

    assert embed.title == "World Clock"
    assert embed.description.index("Los Angeles") < embed.description.index("Tokyo")
    assert "**Los Angeles** | America/Los_Angeles | Thursday February 15 04:00 AM" in embed.description
    assert "**Tokyo** | Asia/Tokyo | Thursday February 15 09:00 PM" in embed.description
    assert embed.footer.text == "DM scope | Updates every minute"
    assert embed.fields[0].name == "Live Status"
    assert "Expires: <t:" in embed.fields[0].value
    assert "Updated: <t:" in embed.fields[0].value


def test_get_world_clock_local_time_uses_reference_time():
    reference_now = datetime(2024, 2, 15, 12, 0, tzinfo=timezone.utc)
    world_clock = WorldClock(guild_id=GUILD_ID, user_id=None, timezone_str="Europe/London", label="London")

    local_time = get_world_clock_local_time(world_clock, now=reference_now)

    assert local_time.tzinfo is not None
    assert format_time(local_time) == "Thursday February 15 12:00 PM"
