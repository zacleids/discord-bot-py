import random
import re

from .errors import InvalidInputError
from .utils import range_validator


def dice_roll_command(args: list[str]) -> str:
    if len(args) == 0:
        raise InvalidInputError(r"Invalid input. please use !r {num}d{num} ie. \`!r 1d20\`")

    dice_regex = r"\d+d\d+"
    number_regex = r"\d+"
    plus_regex = r"\+"
    negative_regex = r"-"

    negative_modifier_on_next_num = False

    rolls = []

    for arg in args:
        if re.match(dice_regex, arg):
            rolls.append(roll_dice(arg, negative_modifier_on_next_num))
            if negative_modifier_on_next_num:
                negative_modifier_on_next_num = False
        elif re.match(number_regex, arg):
            num = int(arg)
            rolls.append([num * -1 if negative_modifier_on_next_num else num])
            if negative_modifier_on_next_num:
                negative_modifier_on_next_num = False
        elif re.match(plus_regex, arg):
            continue
        elif re.match(negative_regex, arg):
            negative_modifier_on_next_num = True
        else:
            raise InvalidInputError(f"Invalid argument received: {arg}")

    flattened_rolls = [r for roll in rolls for r in roll]

    rolled_sum = 0
    for r in flattened_rolls:
        rolled_sum = rolled_sum + int(r)

    if len(flattened_rolls) == 1:
        return str(rolled_sum)

    formatted_rolls = []
    for roll in rolls:
        formatted_rolls.append(roll_format(roll))

    return " + ".join(formatted_rolls) + " = " + str(rolled_sum)


def roll_format(roll: list[int]) -> str:
    if len(roll) == 1:
        return str(roll[0])

    return "(" + " + ".join(map(str, roll)) + ")"


def roll_dice(dice: str, negative_modifier: bool) -> list[int]:
    split_arg = dice.split("d")
    num_dice = int(split_arg[0])
    num_sides = int(split_arg[1])

    dice_lower_bound = 1
    dice_upper_bound = 100

    if not range_validator(num_dice, dice_lower_bound, dice_upper_bound):
        raise InvalidInputError(
            (
                f"I'm sorry, number of dice are out of range. "
                f"Please provide number of dices in the range [{dice_lower_bound}, {dice_upper_bound}]."
            )
        )

    side_lower_bound = 2
    side_upper_bound = 1000

    if not range_validator(num_sides, side_lower_bound, side_upper_bound):
        raise InvalidInputError(
            f"I'm sorry, number of sides of a dice are out of range. "
            f"Please provide number of dices in the range [{side_lower_bound}, {side_upper_bound}]."
        )

    rolls = []
    for i in range(0, num_dice):
        roll = random.randint(1, num_sides)
        if negative_modifier:
            roll = roll * -1
        rolls.append(roll)
    return rolls


def random_command(args: list[str]) -> str:
    if len(args) != 2:
        raise InvalidInputError("Invalid input. Please use random <min> <max>")

    try:
        min_val = float(args[0])
        max_val = float(args[1])
    except ValueError:
        raise InvalidInputError("Both arguments must be numbers.")

    lower = min(min_val, max_val)
    upper = max(min_val, max_val)

    # Check if both are integers (including negative numbers)
    if float(lower).is_integer() and float(upper).is_integer():
        result = random.randint(int(lower), int(upper))
        return str(result)
    else:
        result = random.uniform(lower, upper)
        return str(result)
