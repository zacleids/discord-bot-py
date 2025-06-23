from enum import Enum

from errors import InvalidInputError


class TransformChoice(str, Enum):
    Alternating_case = "alternating_case"
    Mirror = "mirror"
    Reverse = "reverse"
    Upside_down = "upside_down"


# Mapping for upside down characters (bidirectional)
UPSIDE_DOWN_MAP = {
    "a": "ɐ",
    "ɐ": "a",
    "b": "q",
    "q": "b",
    "c": "ɔ",
    "ɔ": "c",
    "d": "p",
    "p": "d",
    "e": "ǝ",
    "ǝ": "e",
    "f": "ɟ",
    "ɟ": "f",
    "g": "ƃ",
    "ƃ": "g",
    "h": "ɥ",
    "ɥ": "h",
    "i": "ᴉ",
    "ᴉ": "i",
    "j": "ɾ",
    "ɾ": "j",
    "k": "ʞ",
    "ʞ": "k",
    "l": "l",
    "m": "ɯ",
    "ɯ": "m",
    "n": "u",
    "u": "n",
    "o": "o",
    "r": "ɹ",
    "ɹ": "r",
    "s": "s",
    "t": "ʇ",
    "ʇ": "t",
    "v": "ʌ",
    "ʌ": "v",
    "w": "ʍ",
    "ʍ": "w",
    "x": "x",
    "y": "ʎ",
    "ʎ": "y",
    "z": "z",
    ".": "˙",
    "˙": ".",
    "!": "¡",
    "¡": "!",
    "?": "¿",
    "¿": "?",
    "[": "]",
    "]": "[",
    "(": ")",
    ")": "(",
    "{": "}",
    "}": "{",
    "<": ">",
    ">": "<",
    "A": "∀",
    "∀": "A",
    "B": "𐐒",
    "𐐒": "B",
    "C": "Ɔ",
    "Ɔ": "C",
    "D": "ᗡ",
    "ᗡ": "D",
    "E": "Ǝ",
    "Ǝ": "E",
    "F": "Ⅎ",
    "Ⅎ": "F",
    "G": "⅁",
    "⅁": "G",
    "H": "H",
    "I": "I",
    "J": "ſ",
    "ſ": "J",
    "K": "ʞ",
    "L": "˥",
    "˥": "L",
    "M": "W",
    "W": "M",
    "N": "N",
    "O": "O",
    "P": "Ԁ",
    "Ԁ": "P",
    "Q": "Ό",
    "Ό": "Q",
    "R": "ᴚ",
    "ᴚ": "R",
    "S": "S",
    "T": "⊥",
    "⊥": "T",
    "U": "∩",
    "∩": "U",
    "V": "Λ",
    "Λ": "V",
    "X": "X",
    "Y": "⅄",
    "⅄": "Y",
    "Z": "Z",
}

# Mapping for mirrored characters (bidirectional)
MIRROR_MAP = {
    "a": "ɒ",
    "ɒ": "a",
    "b": "d",
    "d": "b",
    "c": "ɔ",
    "ɔ": "c",
    "e": "ɘ",
    "ɘ": "e",
    "f": "ꟻ",
    "ꟻ": "f",
    "g": "ǫ",
    "ǫ": "g",
    "h": "ʜ",
    "ʜ": "h",
    "i": "i",
    "j": "ꞁ",
    "ꞁ": "j",
    "k": "ʞ",
    "ʞ": "k",
    "l": "|",
    "|": "l",
    "m": "m",
    "n": "n",
    "o": "o",
    "p": "q",
    "q": "p",
    "r": "ᴙ",
    "ᴙ": "r",
    "s": "ꙅ",
    "ꙅ": "s",
    "t": "ƚ",
    "ƚ": "t",
    "u": "u",
    "v": "v",
    "w": "w",
    "x": "x",
    "y": "y",
    "z": "z",
    ".": ".",
    "!": "!",
    "?": "?",
    "[": "]",
    "]": "[",
    "(": ")",
    ")": "(",
    "{": "}",
    "}": "{",
    "<": ">",
    ">": "<",
    "A": "A",
    "B": "ᙠ",
    "ᙠ": "B",
    "C": "Ɔ",
    "Ɔ": "C",
    "D": "ᗡ",
    "ᗡ": "D",
    "E": "Ǝ",
    "Ǝ": "E",
    "F": "ꟻ",
    "G": "Ꭾ",
    "Ꭾ": "G",
    "H": "H",
    "I": "I",
    "J": "Ⴑ",
    "Ⴑ": "J",
    "K": "ꓘ",
    "ꓘ": "K",
    "L": "⅃",
    "⅃": "L",
    "M": "M",
    "N": "И",
    "И": "N",
    "O": "O",
    "P": "ꟼ",
    "ꟼ": "P",
    "Q": "Ϙ",
    "Ϙ": "Q",
    "R": "Я",
    "Я": "R",
    "S": "Ꙅ",
    "Ꙅ": "S",
    "T": "T",
    "U": "U",
    "V": "V",
    "W": "W",
    "X": "X",
    "Y": "Y",
    "Z": "Ƹ",
    "Ƹ": "Z",
}


def reverse_text(text: str) -> str:
    """Returns the text reversed"""
    return text[::-1]


def mirror_text(text: str) -> str:
    """Returns the text with mirrored characters"""
    return "".join(MIRROR_MAP.get(c, c) for c in text)


def upside_down_text(text: str) -> str:
    """Returns the text flipped upside down"""
    return "".join(UPSIDE_DOWN_MAP.get(c, c) for c in reversed(text))


def alternating_case(text: str) -> str:
    """Returns text with alternating case"""
    return "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(text))


def transform_text(text: str, transform_type: TransformChoice) -> str:
    match transform_type:
        case TransformChoice.Alternating_case:
            return alternating_case(text)
        case TransformChoice.Mirror:
            return mirror_text(text)
        case TransformChoice.Reverse:
            return reverse_text(text)
        case TransformChoice.Upside_down:
            return upside_down_text(text)
        case _:
            return text


def handle_text_transform_command(args: list[str]) -> str:
    """Handle the text transform command with args in format: [transform_type, *text_words]"""
    if len(args) < 2:
        raise InvalidInputError("Usage: !transform <type> <text>")

    try:
        transform_type = TransformChoice(args[0].lower())
    except ValueError:
        valid_types = ", ".join([t.value for t in TransformChoice])
        raise InvalidInputError(f"Invalid transform type. Valid types: {valid_types}")

    text = " ".join(args[1:])
    return transform_text(text, transform_type)
