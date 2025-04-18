from enum import Enum
from discord import app_commands

class UnitCategory(Enum):
    LENGTH = "length"
    MASS = "mass"
    VOLUME = "volume"

class UnitType(Enum):
    # Length
    METER = ("meter", UnitCategory.LENGTH)
    KILOMETER = ("kilometer", UnitCategory.LENGTH)
    CENTIMETER = ("centimeter", UnitCategory.LENGTH)
    MILLIMETER = ("millimeter", UnitCategory.LENGTH)
    MILE = ("mile", UnitCategory.LENGTH)
    YARD = ("yard", UnitCategory.LENGTH)
    FOOT = ("foot", UnitCategory.LENGTH)
    INCH = ("inch", UnitCategory.LENGTH)
    # Mass
    GRAM = ("gram", UnitCategory.MASS)
    KILOGRAM = ("kilogram", UnitCategory.MASS)
    POUND = ("pound", UnitCategory.MASS)
    OUNCE = ("ounce", UnitCategory.MASS)
    # Volume
    LITER = ("liter", UnitCategory.VOLUME)
    MILLILITER = ("milliliter", UnitCategory.VOLUME)
    GALLON = ("gallon", UnitCategory.VOLUME)
    QUART = ("quart", UnitCategory.VOLUME)
    PINT = ("pint", UnitCategory.VOLUME)
    FLUID_OUNCE = ("fluid_ounce", UnitCategory.VOLUME)

    @property
    def category(self):
        return self.value[1]

class UnitTypeChoice(Enum):
    Meter = "Meter"
    Kilometer = "Kilometer"
    Centimeter = "Centimeter"
    Millimeter = "Millimeter"
    Mile = "Mile"
    Yard = "Yard"
    Foot = "Foot"
    Inch = "Inch"
    Gram = "Gram"
    Kilogram = "Kilogram"
    Pound = "Pound"
    Ounce = "Ounce"
    Liter = "Liter"
    Milliliter = "Milliliter"
    Gallon = "Gallon"
    Quart = "Quart"
    Pint = "Pint"
    Fluid_ounce = "Fluid ounce"

# Conversion factors to base units (meter, gram, liter)
CONVERSION_FACTORS = {
    # Length to meter
    UnitType.METER: 1.0,
    UnitType.KILOMETER: 1000.0,
    UnitType.CENTIMETER: 0.01,
    UnitType.MILLIMETER: 0.001,
    UnitType.MILE: 1609.34,
    UnitType.YARD: 0.9144,
    UnitType.FOOT: 0.3048,
    UnitType.INCH: 0.0254,
    # Mass to gram
    UnitType.GRAM: 1.0,
    UnitType.KILOGRAM: 1000.0,
    UnitType.POUND: 453.592,
    UnitType.OUNCE: 28.3495,
    # Volume to liter
    UnitType.LITER: 1.0,
    UnitType.MILLILITER: 0.001,
    UnitType.GALLON: 3.78541,
    UnitType.QUART: 0.946353,
    UnitType.PINT: 0.473176,
    UnitType.FLUID_OUNCE: 0.0295735,
}

# Common names and abbreviations mapping to UnitType
UNIT_ALIASES = {
    # Length
    "m": UnitType.METER,
    "meter": UnitType.METER,
    "meters": UnitType.METER,
    "km": UnitType.KILOMETER,
    "kilometer": UnitType.KILOMETER,
    "kilometers": UnitType.KILOMETER,
    "cm": UnitType.CENTIMETER,
    "centimeter": UnitType.CENTIMETER,
    "centimeters": UnitType.CENTIMETER,
    "mm": UnitType.MILLIMETER,
    "millimeter": UnitType.MILLIMETER,
    "millimeters": UnitType.MILLIMETER,
    "mi": UnitType.MILE,
    "mile": UnitType.MILE,
    "miles": UnitType.MILE,
    "yd": UnitType.YARD,
    "yard": UnitType.YARD,
    "yards": UnitType.YARD,
    "ft": UnitType.FOOT,
    "foot": UnitType.FOOT,
    "feet": UnitType.FOOT,
    "in": UnitType.INCH,
    "inch": UnitType.INCH,
    "inches": UnitType.INCH,
    # Mass
    "g": UnitType.GRAM,
    "gram": UnitType.GRAM,
    "grams": UnitType.GRAM,
    "kg": UnitType.KILOGRAM,
    "kilogram": UnitType.KILOGRAM,
    "kilograms": UnitType.KILOGRAM,
    "lb": UnitType.POUND,
    "lbs": UnitType.POUND,
    "pound": UnitType.POUND,
    "pounds": UnitType.POUND,
    "oz": UnitType.OUNCE,
    "ounce": UnitType.OUNCE,
    "ounces": UnitType.OUNCE,
    # Volume
    "l": UnitType.LITER,
    "liter": UnitType.LITER,
    "liters": UnitType.LITER,
    "ml": UnitType.MILLILITER,
    "milliliter": UnitType.MILLILITER,
    "milliliters": UnitType.MILLILITER,
    "gal": UnitType.GALLON,
    "gallon": UnitType.GALLON,
    "gallons": UnitType.GALLON,
    "qt": UnitType.QUART,
    "quart": UnitType.QUART,
    "quarts": UnitType.QUART,
    "pt": UnitType.PINT,
    "pint": UnitType.PINT,
    "pints": UnitType.PINT,
    "fl_oz": UnitType.FLUID_OUNCE,
    "fl oz": UnitType.FLUID_OUNCE,
    "fluidounce": UnitType.FLUID_OUNCE,
    "fluidounces": UnitType.FLUID_OUNCE,
    "fluid_ounce": UnitType.FLUID_OUNCE,
    "fluid_ounces": UnitType.FLUID_OUNCE,
}

def parse_unit(unit_str: str) -> UnitType:
    key = unit_str.strip().replace(".", "").replace("_", " ").lower()
    key = key.replace(" ", "")  # Remove spaces for keys like 'fluid ounce'
    if key in UNIT_ALIASES:
        return UNIT_ALIASES[key]
    try:
        return UnitType[unit_str.upper()]
    except KeyError:
        raise KeyError(f"Unknown unit: {unit_str}")

def format_unit_name(unit: UnitType) -> str:
    # Capitalize first letter, rest lowercase, replace underscores with spaces if any
    return unit.name.capitalize().replace('_', '_')

def format_unit_category(unit: UnitType) -> str:
    return unit.category.value

def convert_units(from_unit: UnitType, to_unit: UnitType, number: float) -> float:
    if from_unit.category != to_unit.category:
        raise ValueError(f"Incompatible units: {format_unit_name(from_unit)} ({format_unit_category(from_unit)}) and {format_unit_name(to_unit)} ({format_unit_category(to_unit)}).")
    # Convert to base unit
    base_value = number * CONVERSION_FACTORS[from_unit]
    # Convert to target unit
    result = base_value / CONVERSION_FACTORS[to_unit]
    return result

def get_conversion_display(from_unit: UnitType, to_unit: UnitType, number: float, height_display: bool = False) -> str:
    result = convert_units(from_unit, to_unit, number)
    # Format input number to remove unnecessary .0
    if float(number).is_integer():
        number_display = str(int(number))
    else:
        number_display = str(number)
    # Special case: height_display for feet
    if height_display and to_unit == UnitType.FOOT:
        total_inches = result * 12
        feet = int(total_inches // 12)
        inches = round(total_inches % 12)
        return f"{number_display} {format_unit_name(from_unit)} = {feet} ft {inches} in"
    return f"{number_display} {format_unit_name(from_unit)} = {result:.4g} {format_unit_name(to_unit)}"

def handle_conversion_command(args: list[str]) -> str:
    usage = "Usage: !conversion <from_unit> <to_unit> <number> (e.g., !conversion meter foot 10)"
    if len(args) != 3:
        return f"Invalid arguments. {usage}"
    from_unit_str, to_unit_str, number_str = args
    try:
        from_unit = parse_unit(from_unit_str)
        to_unit = parse_unit(to_unit_str)
        number = float(number_str)
    except KeyError:
        return f"Unknown unit. Valid units: {[format_unit_name(u) for u in UnitType]}"
    except ValueError:
        return f"Invalid number: {number_str}"
    try:
        return get_conversion_display(from_unit, to_unit, number, True)
    except ValueError as e:
        return str(e)
