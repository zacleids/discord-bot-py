import pytest

from shared.conversion import UnitType, convert_units, parse_unit


def test_length_conversion():
    assert convert_units(UnitType.METER, UnitType.KILOMETER, 1000) == 1
    assert convert_units(UnitType.MILE, UnitType.FOOT, 1) == pytest.approx(5280, rel=1e-4)


def test_mass_conversion():
    assert convert_units(UnitType.GRAM, UnitType.KILOGRAM, 1000) == 1
    assert convert_units(UnitType.POUND, UnitType.OUNCE, 1) == pytest.approx(16)


def test_volume_conversion():
    assert convert_units(UnitType.LITER, UnitType.MILLILITER, 1) == 1000
    assert convert_units(UnitType.GALLON, UnitType.QUART, 1) == pytest.approx(4)


def test_temperature_conversion():
    assert convert_units(UnitType.CELSIUS, UnitType.FAHRENHEIT, 0) == 32
    assert convert_units(UnitType.KELVIN, UnitType.CELSIUS, 273.15) == pytest.approx(0)


def test_velocity_conversion():
    assert convert_units(UnitType.METER_PER_SECOND, UnitType.KILOMETER_PER_HOUR, 1) == pytest.approx(3.6)
    assert convert_units(UnitType.MILE_PER_HOUR, UnitType.METER_PER_SECOND, 1) == pytest.approx(0.44704)


def test_incompatible_units():
    with pytest.raises(ValueError):
        convert_units(UnitType.METER, UnitType.GRAM, 1)
    with pytest.raises(ValueError):
        convert_units(UnitType.LITER, UnitType.CELSIUS, 1)


def test_parse_unit():
    assert parse_unit("meter") == UnitType.METER
    assert parse_unit("km") == UnitType.KILOMETER
    with pytest.raises(KeyError):
        parse_unit("unknown_unit")


def test_imperial_to_metric_conversion():
    assert convert_units(UnitType.MILE, UnitType.KILOMETER, 1) == pytest.approx(1.60934)
    assert convert_units(UnitType.FOOT, UnitType.METER, 1) == pytest.approx(0.3048)


def test_metric_to_imperial_conversion():
    assert convert_units(UnitType.KILOMETER, UnitType.MILE, 1) == pytest.approx(0.621371, rel=1e-5)
    assert convert_units(UnitType.METER, UnitType.FOOT, 1) == pytest.approx(3.28084)
