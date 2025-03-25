import re
from random import randrange

from PIL import Image, ImageColor
from pathlib import Path

from errors import InvalidInputError

Path("temp/").mkdir(parents=True, exist_ok=True)
# Setting the size of the image
size = (400, 300)

image_name_start = 'temp/new_image'
image_file_type = ".png"


def is_valid_hex_code(hex_code: str) -> bool:
    if hex_code.startswith("#"):
        hex_code = hex_code[1:]

    if len(hex_code) != 6:
        return False

    color_regex = r"(?:[0-9a-fA-F]{3}){1,2}$"
    return bool(re.match(color_regex, hex_code))


def generate_image(color, num=0) -> str:
    # Creating a new image with RGB mode
    new_image = Image.new('RGB', size, color)

    image_name = image_name_start + str(num) + image_file_type
    # Save the image
    new_image.save(image_name)

    return image_name


def formate_rgb_tuple(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2]).upper()


def generate_random_color() -> tuple[int, int, int]:
    r = randrange(255)
    g = randrange(255)
    b = randrange(255)
    return r, g, b


def handle_color_command(args: list[str]):
    result = None
    files = []
    if not args:
        rand_color = generate_random_color()
        generate_image(rand_color)
        result = formate_rgb_tuple(rand_color)
    else:
        subcommand = args[0].lower()
        sub_args = args[1:]

        if len(sub_args) > 1:
            raise InvalidInputError("Invalid args")

        match subcommand:
            case "random" | "rand" | "r":
                num_colors = 1

                if sub_args and sub_args[0] and not sub_args[0].isdigit():
                    raise InvalidInputError("Must provide a digit for number of colors up to 10")
                elif sub_args and sub_args[0]:
                    num_colors = int(sub_args[0])

                if num_colors > 10:
                    raise InvalidInputError("Can only generate up to 10 colors at once")
                result = ""
                for i in range(0, num_colors):
                    rand_color = generate_random_color()
                    files.append(generate_image(rand_color, i))
                    result = result + formate_rgb_tuple(rand_color) + "\n"
            case _:
                if is_valid_hex_code(subcommand):
                    if len(subcommand) == 6:
                        subcommand = "#" + subcommand
                    files.append(generate_image(subcommand))
                    result = subcommand.upper()
                else:
                    try:
                        files.append(generate_image(subcommand))
                        hex_code = ImageColor.getrgb(subcommand)
                        result = subcommand + " " + formate_rgb_tuple(hex_code)
                    except ValueError:
                        raise InvalidInputError(f"Invalid color: {subcommand}")
    return result, files
