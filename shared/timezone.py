from pytz import all_timezones

from .errors import InvalidInputError

all_timezones_lower = list(map(str.lower, all_timezones))


def return_all_timezones():
    return all_timezones + all_timezones_lower


def get_valid_timezone(zone: str) -> str:
    normalized_zone = zone.strip()
    if normalized_zone in all_timezones:
        return normalized_zone

    normalized_zone_lower = normalized_zone.lower()
    if normalized_zone_lower in all_timezones_lower:
        return all_timezones[all_timezones_lower.index(normalized_zone_lower)]

    raise InvalidInputError("Timezone not found")
