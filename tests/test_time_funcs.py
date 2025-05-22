import pytest
from time_funcs import add_timezone, remove_timezone, list_timezones, get_valid_timezone, update_timezone, InvalidInputError, WorldClock, format_time

@pytest.fixture(autouse=True)
def setup_function():
    # Clear WorldClock table before each test
    WorldClock.delete().execute()

def test_add_timezone():
    guild_id = 1
    tz = "America/Denver"
    msg = add_timezone(guild_id, tz)
    assert "added" in msg.lower()
    # Should be in the list
    tzs = list_timezones(guild_id)
    assert any(t.timezone_str == tz for t in tzs)

def test_remove_timezone():
    guild_id = 2
    tz = "America/Chicago"
    add_timezone(guild_id, tz)
    msg = remove_timezone(guild_id, tz)
    assert "removed" in msg.lower()
    # Should not be in the list
    tzs = list_timezones(guild_id)
    assert all(t.timezone_str != tz for t in tzs)

def test_update_timezone_label():
    guild_id = 3
    tz = "America/New_York"
    add_timezone(guild_id, tz)
    update_timezone(guild_id, tz, label="NYC")
    tzs = list_timezones(guild_id)
    assert tzs[0].label == "NYC"

def test_list_timezones():
    guild_id = 4
    tz1 = "America/Los_Angeles"
    tz2 = "Europe/London"
    add_timezone(guild_id, tz1)
    add_timezone(guild_id, tz2)
    tzs = list_timezones(guild_id)
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
    guild_id = 1
    tz = "America/Los_Angeles"
    msg1 = add_timezone(guild_id, tz)
    msg2 = add_timezone(guild_id, tz)
    assert "added" in msg1.lower()
    assert "already exists" in msg2.lower()

def test_remove_nonexistent_timezone():
    guild_id = 2
    tz = "America/New_York"
    msg = remove_timezone(guild_id, tz)
    assert "not found" in msg.lower()

def test_case_insensitive_timezone_add_remove():
    guild_id = 3
    tz = "America/Los_Angeles"
    tz_lower = "america/los_angeles"
    msg1 = add_timezone(guild_id, tz)
    assert "added" in msg1.lower()
    # Remove using lower case
    tz_valid = get_valid_timezone(tz_lower)
    msg2 = remove_timezone(guild_id, tz_valid)
    assert "removed" in msg2.lower()

def test_invalid_timezone():
    guild_id = 4
    with pytest.raises(InvalidInputError):
        get_valid_timezone("Not/AZone")


def test_list_timezones_empty():
    guild_id = 5
    tzs = list_timezones(guild_id)
    assert tzs == []

def test_update_label_nonexistent_timezone():
    guild_id = 6
    tz = "America/Chicago"
    # Should not throw
    update_timezone(guild_id, tz, label="Central")
    # Should still not exist
    assert list_timezones(guild_id) == []

def test_add_timezone_with_label_response():
    guild_id = 21
    tz = "Asia/Tokyo"
    label = "Japan Time"
    msg = add_timezone(guild_id, tz, label=label)
    assert "added" in msg.lower()
    assert f"with label {label}" in msg

def test_format_time_output():
    from datetime import datetime
    dt = datetime(2024, 2, 15, 0, 22)  # Thursday February 15 12:22 AM
    formatted = format_time(dt)
    assert formatted == "Thursday February 15 12:22 AM"

def test_get_valid_timezone_canonical():
    tz = get_valid_timezone("Europe/London")
    assert tz == "Europe/London"

def test_get_valid_timezone_lowercase():
    tz = get_valid_timezone("europe/london")
    assert tz == "Europe/London"

def test_get_valid_timezone_invalid():
    with pytest.raises(InvalidInputError):
        get_valid_timezone("fake/timezone")