import datetime
import json
from unittest.mock import MagicMock, patch

import pytest

from shared import currency
from shared.models import CurrencyRate

RATES = {"USD": 1.0, "EUR": 0.9, "MXN": 17.0, "JPY": 155.0}

FAKE_NOW = datetime.datetime(2025, 5, 25, tzinfo=datetime.timezone.utc)


# Helper for mock API response
def mock_response(json_data, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    return mock


def add_currency_rate_to_db(base_currency=currency.BASE_CURRENCY, rates=RATES, last_updated=None):
    """Helper function to add a currency rate entry to the database."""
    if last_updated is None:
        last_updated = FAKE_NOW - datetime.timedelta(hours=1)

    CurrencyRate.create(base_currency=base_currency, rates_json=json.dumps(rates), last_updated=last_updated)


@pytest.fixture(autouse=True)
def setup_function():
    # Clear CurrencyRate table before each test
    CurrencyRate.delete().execute()


@pytest.fixture(autouse=True)
def patch_utcnow():
    with patch("shared.currency.utcnow", return_value=FAKE_NOW):
        yield


@patch("shared.currency.requests.get")
def test_fetch_and_store_rates_success(mock_get):
    data = {"result": "success", "rates": RATES}
    mock_get.return_value = mock_response(data)
    # Remove any existing rates
    CurrencyRate.delete().execute()
    rates = currency.fetch_and_store_rates()
    assert rates == data["rates"]
    db_entry = CurrencyRate.select().where(CurrencyRate.base_currency == currency.BASE_CURRENCY).first()
    assert db_entry is not None
    assert json.loads(db_entry.rates_json) == data["rates"]


@patch("shared.currency.requests.get")
def test_fetch_and_store_rates_failure_result(mock_get):
    data = {"result": "error", "error-type": "bad-request"}
    mock_get.return_value = mock_response(data)
    with pytest.raises(Exception, match="Failed to fetch exchange rates"):
        currency.fetch_and_store_rates()


@patch("shared.currency.requests.get")
def test_fetch_and_store_rates_500_error(mock_get):
    mock_get.side_effect = Exception("Server error")
    with pytest.raises(Exception, match="Server error"):
        currency.fetch_and_store_rates()


@patch("shared.currency.fetch_and_store_rates")
def test_convert_currency_no_db_entry(mock_fetch):
    mock_fetch.return_value = RATES
    result = currency.convert_currency("USD", "EUR", 10)
    assert result == 9.0
    mock_fetch.assert_called_once()


@patch("shared.currency.fetch_and_store_rates")
def test_convert_currency_expired_entry(mock_fetch):
    # Add an expired entry
    old = FAKE_NOW - datetime.timedelta(hours=25)
    add_currency_rate_to_db(last_updated=old.replace(tzinfo=None))
    mock_fetch.return_value = RATES
    result = currency.convert_currency("USD", "EUR", 10)
    assert result == 9.0
    mock_fetch.assert_called_once()
    # Ensure only one entry remains
    assert CurrencyRate.select().count() == 1


@patch("shared.currency.fetch_and_store_rates")
def test_convert_currency_recent_entry(mock_fetch):
    # Add a recent entry
    add_currency_rate_to_db()
    result = currency.convert_currency("USD", "EUR", 10)
    assert result == 9.0
    mock_fetch.assert_not_called()
    # Ensure only one entry remains
    assert CurrencyRate.select().count() == 1


@patch("shared.currency.fetch_and_store_rates")
def test_convert_usd_to_mxn(mock_fetch):
    add_currency_rate_to_db()
    result = currency.convert_currency("USD", "MXN", 10)
    assert result == 170.0
    mock_fetch.assert_not_called()


@patch("shared.currency.fetch_and_store_rates")
def test_convert_usd_to_eur(mock_fetch):
    add_currency_rate_to_db()
    result = currency.convert_currency("USD", "EUR", 10)
    assert result == 9.0
    mock_fetch.assert_not_called()


@patch("shared.currency.fetch_and_store_rates")
def test_convert_mxn_to_jpy(mock_fetch):
    add_currency_rate_to_db()
    result = currency.convert_currency("MXN", "JPY", 10)
    assert pytest.approx(result, 0.01) == 91.18
    mock_fetch.assert_not_called()
