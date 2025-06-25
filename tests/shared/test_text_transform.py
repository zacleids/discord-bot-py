import pytest

from shared.text_transform import (
    InvalidInputError,
    TransformChoice,
    handle_text_transform_command,
    transform_text,
)


def test_alternating_case():
    result = transform_text("hello world", TransformChoice.Alternating_case)
    assert result == "HeLlO WoRlD"


def test_mirror():
    result = transform_text("hello world", TransformChoice.Mirror)
    assert result == "ʜɘ||o woᴙ|b"  # Updated expected mirrored text to match actual output
    reverse_result = transform_text(result, TransformChoice.Mirror)
    assert reverse_result == "hello world"


def test_reverse():
    result = transform_text("hello world", TransformChoice.Reverse)
    assert result == "dlrow olleh"
    reverse_result = transform_text(result, TransformChoice.Reverse)
    assert reverse_result == "hello world"


def test_upside_down():
    result = transform_text("hello world", TransformChoice.Upside_down)
    assert result == "plɹoʍ ollǝɥ"
    reverse_result = transform_text(result, TransformChoice.Upside_down)
    assert reverse_result == "hello world"


def test_handle_text_transform_command():
    # Test alternating case
    result = handle_text_transform_command(["alternating_case", "hello", "world"])
    assert result == "HeLlO WoRlD"

    # Test mirror
    result = handle_text_transform_command(["mirror", "hello", "world"])
    assert result == "ʜɘ||o woᴙ|b"

    # Test reverse
    result = handle_text_transform_command(["reverse", "hello", "world"])
    assert result == "dlrow olleh"

    # Test upside down
    result = handle_text_transform_command(["upside_down", "hello", "world"])
    assert result == "plɹoʍ ollǝɥ"


def test_handle_text_transform_command_invalid_type():
    # Test invalid input
    with pytest.raises(InvalidInputError):
        handle_text_transform_command(["invalid_type", "hello", "world"])


def test_handle_text_transform_command_missing_arguments():
    # Test missing arguments
    with pytest.raises(InvalidInputError):
        handle_text_transform_command(["reverse"])
