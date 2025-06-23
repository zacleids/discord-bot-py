import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # This line is necessary to import the module from the parent directory

import pytest
from color import is_valid_hex_code, formate_rgb_tuple, generate_random_color, handle_color_command
from errors import InvalidInputError


# Test is_valid_hex_code
@pytest.mark.parametrize(
    "hex_code,expected",
    [
        ("#FFFFFF", True),
        ("#000000", True),
        ("FFFFFF", True),
        ("000000", True),
        ("#FFF", False),
        ("FFF", False),
        ("#GGGGGG", False),
        ("12345", False),
        ("#1234567", False),
        ("", False),
        ("hello", False),
        ("#123", False),
        ("#123456", True),
        ("#123abc", True),
        ("#ABCDEF", True),
        ("#abcdef", True),
        ("#1234567890", False),
        ("#12G456", False),
        ("#12345G", False),
        ("#1234", False),
        ("#12", False),
        ("#1", False),
        ("#", False),
    ],
)
def test_is_valid_hex_code(hex_code, expected):
    assert is_valid_hex_code(hex_code) == expected


# Test formate_rgb_tuple
@pytest.mark.parametrize(
    "rgb,expected",
    [
        ((255, 255, 255), "#FFFFFF"),
        ((0, 0, 0), "#000000"),
        ((17, 34, 51), "#112233"),
        ((255, 0, 0), "#FF0000"),
        ((0, 255, 0), "#00FF00"),
        ((0, 0, 255), "#0000FF"),
        ((255, 255, 0), "#FFFF00"),
        ((255, 0, 255), "#FF00FF"),
        ((0, 255, 255), "#00FFFF"),
        ((128, 128, 128), "#808080"),
        ((192, 192, 192), "#C0C0C0"),
        ((123, 234, 56), "#7BEA38"),
    ],
)
def test_formate_rgb_tuple(rgb, expected):
    assert formate_rgb_tuple(rgb) == expected


# Test generate_random_color returns valid RGB tuple
def test_generate_random_color():
    rgb = generate_random_color()
    assert isinstance(rgb, tuple)
    assert len(rgb) == 3
    assert all(0 <= c < 255 for c in rgb)


# Test handle_color_command with random color
def test_handle_color_command_random():
    result, files = handle_color_command(["random", "1"])
    assert result.startswith("#")
    assert len(files) == 1
    assert files[0].endswith(".png")


# Test handle_color_command with named color
def test_handle_color_command_named():
    result, files = handle_color_command(["red"])
    assert "#FF0000" in result or "red" in result.lower()
    assert len(files) == 1
    assert files[0].endswith(".png")


# Test handle_color_command with hex color
def test_handle_color_command_hex():
    result, files = handle_color_command(["#AA00BB"])
    assert result == "#AA00BB"
    assert len(files) == 1
    assert files[0].endswith(".png")


# Test handle_color_command with include_inverted flag
def test_handle_color_command_inverted():
    result, files = handle_color_command(["blue", "include_inverted:true"])
    assert "Inverse Hex:" in result
    assert len(files) == 2
    assert any("inverted" in f for f in files)


# Test handle_color_command with include_inverted:true syntax
def test_handle_color_command_inverted_colon():
    result, files = handle_color_command(["green", "include_inverted:true"])
    assert "Inverse Hex:" in result
    assert len(files) == 2
    assert any("inverted" in f for f in files)


# Test handle_color_command with include_inverted true syntax
def test_handle_color_command_inverted_space():
    result, files = handle_color_command(["green", "include_inverted", "true"])
    assert "Inverse Hex:" in result
    assert len(files) == 2
    assert any("inverted" in f for f in files)


# Test handle_color_command with negative number of colors
@pytest.mark.parametrize("n", ["-1", "-5"])
def test_handle_color_command_negative_colors(n):
    with pytest.raises(InvalidInputError):
        handle_color_command(["random", n])


# Test include_inverted true with multiple colors returns warning
@pytest.mark.parametrize("args", [["random", "3", "include_inverted:true"], ["random", "3", "include_inverted", "true"]])
def test_handle_color_command_inverted_multiple_colors(args):
    result, files = handle_color_command(args)
    assert "Warning: Inverted color does not work with multiple colors at once" in result
    assert len(files) == 3
    assert all("inverted" not in f for f in files)


# Test handle_color_command with too many colors
def test_handle_color_command_too_many():
    with pytest.raises(InvalidInputError):
        handle_color_command(["random", "11"])


# Test handle_color_command with invalid color
def test_handle_color_command_invalid():
    with pytest.raises(InvalidInputError):
        handle_color_command(["notacolor"])
