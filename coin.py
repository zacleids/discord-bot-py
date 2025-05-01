import random

from errors import InvalidInputError
from utils import is_numeric


def flip_coin() -> str:
    return random.choices(["heads", "tails", "Wow, it landed on its edge! Weird right?"], weights=[49.5, 49.5, 1])[0]


def flip_coins(args: list[str]) -> str:
    if len(args) != 1:
        raise InvalidInputError("Invalid input. Provide exactly one argument.")

    num = None
    try:
        num = int(args[0])
    except ValueError:
        raise InvalidInputError("Invalid input. Provide a valid integer.")

    if not is_numeric(args[0]) or num < 1 or num > 100000:
        raise InvalidInputError("Invalid input. Enter a positive number less than or equal to 100,000.")

    if num == 1:
        return flip_coin()

    if num < 25:
        arr = []
        for i in range(0, num):
            arr.append(random.choice(["H", "T"]))
        return "".join(arr)

    count = 0
    for _ in range(0, num):
        count = count + random.getrandbits(1)

    return f"Heads: {count}\nTails: {num - count}"
