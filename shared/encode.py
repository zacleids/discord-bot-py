import base64
import codecs
from enum import Enum

# Morse code dictionary
MORSE_CODE_DICT = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    "0": "-----",
    " ": " ",
}

MORSE_CODE_REVERSE = {value: key for key, value in MORSE_CODE_DICT.items()}


class EncoderChoice(Enum):
    Base64 = "base64"
    Binary = "binary"
    Morse = "morse"
    ROT13 = "rot13"
    All = "all"


class EncoderChoiceWithoutAll(Enum):
    Base64 = "base64"
    Binary = "binary"
    Morse = "morse"
    ROT13 = "rot13"


def encode_binary(text):
    return " ".join(format(ord(char), "08b") for char in text)


def decode_binary(binary):
    binary = binary.replace(" ", "")
    return "".join(chr(int(binary[i : i + 8], 2)) for i in range(0, len(binary), 8))


def encode_base64(text):
    return base64.b64encode(text.encode()).decode()


def decode_base64(text):
    return base64.b64decode(text.encode()).decode()


def encode_rot13(text):
    return codecs.encode(text, "rot_13")


def decode_rot13(text):
    return codecs.decode(text, "rot_13")


def encode_morse(text):
    return " ".join(MORSE_CODE_DICT.get(char.upper(), "") for char in text)


def decode_morse(text):
    return "".join(MORSE_CODE_REVERSE.get(code, "") for code in text.split())


methods = {
    EncoderChoice.Binary.value: (encode_binary, decode_binary),
    EncoderChoice.Base64.value: (encode_base64, decode_base64),
    EncoderChoice.ROT13.value: (encode_rot13, decode_rot13),
    EncoderChoice.Morse.value: (encode_morse, decode_morse),
}


def encode_decode(text, method, operation="encode"):
    if method not in methods:
        raise ValueError(f"Unknown method: {method}")

    encode_func, decode_func = methods[method]
    return encode_func(text) if operation == "encode" else decode_func(text)


def handle_encode_decode_command(args: list[str], operation: str) -> str:
    result = None
    available_methods = ", ".join(list(methods.keys()) + ["all"])
    usage_example = "Usage: !encode <method> <text> (e.g., !encode base64 hello world)"
    if not args:
        result = f"Please provide an encode/decode method. Available methods: {available_methods}. {usage_example}"
    else:
        method = args[0].lower() if len(args) > 0 else None

        if method not in methods and method != "all":
            raise ValueError(f"Unknown method: {method}. Available methods are: {available_methods}")

        text = " ".join(args[1:])
        if not len(text) > 0:
            raise ValueError(f"No text to encode/decode provided. {usage_example}")

        try:
            if method == "all" and operation == "encode":
                result = "\n".join([f"`{m.capitalize()} encoded:` {encode_decode(text, m, operation)}" for m in methods])
            else:
                result = encode_decode(text, method, operation)
                result = f"`{method} text:` {text}\n`{operation.capitalize()}d Text:` {result}"
        except Exception:
            result = f"Invalid input `{text}` provided to `{method}` {operation}, please provide valid input."

    return f"{result}"
