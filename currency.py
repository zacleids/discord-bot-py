from enum import Enum
import pytz
import requests
import datetime
from models import CurrencyRate, orm_db
from utils import format_number
from log import log_event, get_ray_id

import datetime
import json


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


# Add property methods to CurrencyRate for JSON and datetime handling


def _get_rates(self):
    return json.loads(self.rates_json)


def _set_rates(self, value):
    self.rates_json = json.dumps(value)


@property
def rates(self):
    return _get_rates(self)


@rates.setter
def rates(self, value):
    _set_rates(self, value)


CurrencyRate.rates = rates

CURRENCY_NAMES = {
    "USD": "US Dollar",
    "MXN": "Mexican Peso",
    "CAD": "Canadian Dollar",
    "EUR": "Euro",
    "GBP": "British Pound",
    "JPY": "Japanese Yen",
    "AUD": "Australian Dollar",
    "ILS": "Israeli New Shekel",
    "INR": "Indian Rupee",
    "BRL": "Brazilian Real",
    "ARS": "Argentine Peso",
    "VES": "Venezuelan Bolívar",
    "PEN": "Peruvian Sol",
    "SGD": "Singapore Dollar",
    "CHF": "Swiss Franc",
    "HKD": "Hong Kong Dollar",
    "KRW": "South Korean Won",
    "CNY": "Chinese Yuan",
    "SEK": "Swedish Krona",
    "NOK": "Norwegian Krone",
    "NZD": "New Zealand Dollar",
    "PHP": "Philippine Peso",
    "TWD": "New Taiwan Dollar",
}


def get_currency_name(code: str) -> str:
    """Get the full name of a currency given its code."""
    return CURRENCY_NAMES.get(code, code)


# provided free without API key from https://www.exchangerate-api.com/docs/free
API_URL = "https://open.er-api.com/v6/latest/"

REFRESH_HOURS = 24

BASE_CURRENCY = "USD"


# Only fetch/store rates with USD as base currency
def fetch_and_store_rates() -> dict:
    """Fetch exchange rates from the API and store them in the database."""
    url = API_URL + BASE_CURRENCY
    ray_id = get_ray_id()
    log_event(
        "CURRENCY_API_REQUEST",
        {"event": "CURRENCY_API_REQUEST", "url": url, "base_currency": BASE_CURRENCY, "ray_id": ray_id},
        level="info",
    )
    response = requests.get(url)
    data = response.json()
    if data["result"] != "success":
        log_event(
            "CURRENCY_API_ERROR",
            {"event": "CURRENCY_API_ERROR", "url": url, "base_currency": BASE_CURRENCY, "response": data, "ray_id": ray_id},
            level="error",
        )
        raise Exception("Failed to fetch exchange rates.")
    rates = data["rates"]
    now = utcnow()
    with orm_db.atomic():
        CurrencyRate.delete().where(CurrencyRate.base_currency == BASE_CURRENCY).execute()
        CurrencyRate.create(base_currency=BASE_CURRENCY, rates_json=json.dumps(rates), last_updated=now)
    log_event(
        "CURRENCY_API_SUCCESS",
        {
            "event": "CURRENCY_API_SUCCESS",
            "base_currency": BASE_CURRENCY,
            "fetched_at": str(now),
            "rate_count": len(rates),
            "ray_id": ray_id,
        },
        level="info",
    )
    return rates


def get_rates() -> dict:
    """Get the latest exchange rates from the database or fetch them if outdated."""
    rate = CurrencyRate.select().where(CurrencyRate.base_currency == BASE_CURRENCY).first()
    now = utcnow()
    ray_id = get_ray_id()
    if not rate:
        log_event("CURRENCY_CACHE_MISS", {"event": "CURRENCY_CACHE_MISS", "base_currency": BASE_CURRENCY, "ray_id": ray_id}, level="info")
        return fetch_and_store_rates()
    # Make sure the last_updated is using UTC timezone to compare with now
    last_updated = rate.last_updated
    last_updated_tzaware = last_updated.replace(tzinfo=pytz.UTC)
    age_seconds = (now - last_updated_tzaware).total_seconds()
    if age_seconds > REFRESH_HOURS * 3600:
        log_event(
            "CURRENCY_CACHE_EXPIRED",
            {
                "event": "CURRENCY_CACHE_EXPIRED",
                "base_currency": BASE_CURRENCY,
                "last_updated": str(last_updated_tzaware),
                "age_seconds": age_seconds,
                "ray_id": ray_id,
            },
            level="info",
        )
        return fetch_and_store_rates()
    log_event(
        "CURRENCY_CACHE_HIT",
        {
            "event": "CURRENCY_CACHE_HIT",
            "base_currency": BASE_CURRENCY,
            "last_updated": str(last_updated_tzaware),
            "age_seconds": age_seconds,
            "ray_id": ray_id,
        },
        level="debug",
    )
    return rate.rates


def convert_currency(from_currency: str, to_currency: str, amount: float) -> float:
    """Convert currency from one type to another using the latest exchange rates."""
    ray_id = get_ray_id()
    log_event(
        "CURRENCY_CONVERT",
        {"event": "CURRENCY_CONVERT", "from_currency": from_currency, "to_currency": to_currency, "amount": amount, "ray_id": ray_id},
        level="debug",
    )
    rates = get_rates()
    if from_currency not in rates or to_currency not in rates:
        log_event(
            "CURRENCY_CONVERT_ERROR",
            {
                "event": "CURRENCY_CONVERT_ERROR",
                "from_currency": from_currency,
                "to_currency": to_currency,
                "amount": amount,
                "reason": "Currency not supported",
                "ray_id": ray_id,
            },
            level="error",
        )
        raise Exception(f"Currency not supported.")
    # Convert from source to USD, then USD to target
    amount_in_usd = amount / rates[from_currency] if from_currency != BASE_CURRENCY else amount
    result = amount_in_usd * rates[to_currency] if to_currency != BASE_CURRENCY else amount_in_usd
    log_event(
        "CURRENCY_CONVERT_RESULT",
        {
            "event": "CURRENCY_CONVERT_RESULT",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount": amount,
            "result": result,
            "ray_id": ray_id,
        },
        level="debug",
    )
    return result


def handle_currency_command(args: list[str]) -> str:
    """Handle the currency conversion command."""
    usage = "Usage: !currency <from_currency> <to_currency> <amount> (e.g., !currency USD EUR 10)"
    # Secret list option
    if args and args[0].lower() == "list":
        lines = ["```Code | Name", "----------------------------"]
        for code in CURRENCY_NAMES.keys():
            lines.append(f"{code}  | {get_currency_name(code)}")
        return "Supported currencies:\n" + "\n".join(lines) + "```"

    # Normal conversion
    if len(args) != 3:
        return f"Invalid arguments. {usage}"
    from_cur, to_cur, amt = args
    try:
        from_currency = from_cur.upper()
        to_currency = to_cur.upper()
        amount = float(amt)
        if from_currency not in CURRENCY_NAMES or to_currency not in CURRENCY_NAMES:
            raise KeyError
    except KeyError:
        return f"Unknown currency. Supported: {list(CURRENCY_NAMES.keys())}"
    except ValueError:
        return f"Invalid amount: {amt}"
    try:
        result = convert_currency(from_currency, to_currency, amount)
        return f"{format_number(amount)} {from_currency} = {format_number(result)} {to_currency}"
    except Exception as e:
        return str(e)
