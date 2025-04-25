from enum import Enum
from discord import app_commands
from utils import format_number

class UnitCategory(Enum):
    LENGTH = "length"
    MASS = "mass"
    VOLUME = "volume"
    TEMPERATURE = "temperature"

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
    # Temperature
    CELSIUS = ("celsius", UnitCategory.TEMPERATURE)
    FAHRENHEIT = ("fahrenheit", UnitCategory.TEMPERATURE)
    KELVIN = ("kelvin", UnitCategory.TEMPERATURE)

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
    Celsius = "Celsius"
    Fahrenheit = "Fahrenheit"
    Kelvin = "Kelvin"

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
    # Temperature handled separately
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
    # Temperature
    "c": UnitType.CELSIUS,
    "celsius": UnitType.CELSIUS,
    "centigrade": UnitType.CELSIUS,
    "f": UnitType.FAHRENHEIT,
    "fahrenheit": UnitType.FAHRENHEIT,
    "k": UnitType.KELVIN,
    "kelvin": UnitType.KELVIN,
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

def format_unit_name(unit: UnitType, value: float = 1) -> str:
    # Capitalize first letter, rest lowercase, replace underscores with spaces if any
    name = unit.name.capitalize().replace('_', ' ')

    if abs(value) != 1:
        name += "s"
    # Handle special case for fluid ounce
    if name == "Fluid ounce" and abs(value) != 1:
        name = "Fluid Ounces"
    # Handle special case for feet
    if name == "Foot" and abs(value) != 1:
        name = "Feet"
    return name

def format_unit_category(unit: UnitType) -> str:
    return unit.category.value

def convert_temperature(from_unit: UnitType, to_unit: UnitType, number: float) -> float:
    if from_unit == UnitType.CELSIUS:
        if to_unit == UnitType.FAHRENHEIT:
            return number * 9/5 + 32
        elif to_unit == UnitType.KELVIN:
            return number + 273.15
        else:
            return number
    elif from_unit == UnitType.FAHRENHEIT:
        if to_unit == UnitType.CELSIUS:
            return (number - 32) * 5/9
        elif to_unit == UnitType.KELVIN:
            return (number - 32) * 5/9 + 273.15
        else:
            return number
    elif from_unit == UnitType.KELVIN:
        if to_unit == UnitType.CELSIUS:
            return number - 273.15
        elif to_unit == UnitType.FAHRENHEIT:
            return (number - 273.15) * 9/5 + 32
        else:
            return number
    else:
        raise ValueError("Unknown temperature unit.")

def convert_units(from_unit: UnitType, to_unit: UnitType, number: float) -> float:
    if from_unit.category != to_unit.category:
        raise ValueError(f"Incompatible units: {format_unit_name(from_unit)} ({format_unit_category(from_unit)}) and {format_unit_name(to_unit)} ({format_unit_category(to_unit)}).")
    if from_unit.category == UnitCategory.TEMPERATURE:
        return convert_temperature(from_unit, to_unit, number)
    # Convert to base unit
    base_value = number * CONVERSION_FACTORS[from_unit]
    # Convert to target unit
    result = base_value / CONVERSION_FACTORS[to_unit]
    return result

def get_conversion_display(from_unit: UnitType, to_unit: UnitType, number: float, height_display: bool = False, feet_inches_input: tuple[int, int] = None) -> str:
    result = convert_units(from_unit, to_unit, number)
    number_display = format_number(number)

    # Special formatting for temperature
    if from_unit.category == UnitCategory.TEMPERATURE and to_unit.category == UnitCategory.TEMPERATURE:
        unit_symbols = {
            UnitType.CELSIUS: "°C",
            UnitType.FAHRENHEIT: "°F",
            UnitType.KELVIN: "°K"
        }
        from_symbol = unit_symbols.get(from_unit, from_unit.name)
        to_symbol = unit_symbols.get(to_unit, to_unit.name)
        return f"{number_display}{from_symbol} = {format_number(result)}{to_symbol}"

    # Special case: height_display for feet
    if height_display and to_unit == UnitType.FOOT:
        total_inches = result * 12
        feet = int(total_inches // 12)
        inches = round(total_inches % 12)
        # If input was feet/inches, display as 6 ft 2 in = 188 cm
        if feet_inches_input:
            f, i = feet_inches_input
            if i:
                left = f"{f} ft {i} in"
            else:
                left = f"{f} ft"
            right = f"{format_number(result)} {format_unit_name(to_unit, result)}"
            return f"{left} = {right}"
        return f"{number_display} {format_unit_name(from_unit, number)} = {feet} ft {inches} in"
    
    # If input was feet/inches, display as 6' 2" = 188 cm
    if feet_inches_input:
        f, i = feet_inches_input
        if i:
            left = f"{f} ft {i} in"
        else:
            left = f"{f} ft"
        right = f"{format_number(result)} {format_unit_name(to_unit, result)}"
        return f"{left} = {right}"
    
    return f"{number_display} {format_unit_name(from_unit, number)} = {format_number(result)} {format_unit_name(to_unit, result)}"

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
