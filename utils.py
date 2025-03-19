import re


def is_numeric(value: str) -> bool:
    """
    Check if a value is numeric, including strings with scientific notation.
    """
    return bool(re.match(r"^-?\d+(\.\d+)?([eE]-?\d+)?$", value))


def range_validator(num: int, lower_bound: int, upper_bound: int) -> bool:
    return (num >= lower_bound) and (num <= upper_bound)
