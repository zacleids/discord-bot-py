from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

import shared.fortune as fortune


@pytest.fixture(autouse=True)
def clear_fortune_counter():
    fortune._fortune_counter.clear()


def test_get_fortune_uses_configured_home_timezone_for_today(monkeypatch):
    fixed_now = datetime(2026, 4, 5, 6, 30, tzinfo=ZoneInfo("UTC"))

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return fixed_now.replace(tzinfo=None)
            return fixed_now.astimezone(tz)

    monkeypatch.setattr(fortune, "datetime", FixedDateTime)

    monkeypatch.setattr(fortune.config, "home_timezone", "US/Pacific")
    pacific_fortune = fortune.get_fortune(1234)

    monkeypatch.setattr(fortune.config, "home_timezone", "Asia/Tokyo")
    tokyo_fortune = fortune.get_fortune(1234)

    assert pacific_fortune == fortune._get_deterministic_fortune(1234, "2026-04-04")
    assert tokyo_fortune == fortune._get_deterministic_fortune(1234, "2026-04-05")


def test_get_fortune_explicit_date_ignores_home_timezone(monkeypatch):
    monkeypatch.setattr(fortune.config, "home_timezone", "Asia/Tokyo")

    result = fortune.get_fortune(4321, date="2026-04-05")

    assert result == fortune._get_deterministic_fortune(4321, "2026-04-05")
