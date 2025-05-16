import pytest
from dice import dice_roll_command, roll_dice, random_command
from errors import InvalidInputError

def test_dice_roll_command_single_roll():
    result = dice_roll_command(["1d6"])
    assert not result.startswith("(")
    assert result.isdigit()

def test_dice_roll_command_multiple_rolls():
    result = dice_roll_command(["2d6", "+", "3"])
    assert result.startswith("(")
    assert "=" in result

def test_dice_roll_command_invalid():
    with pytest.raises(InvalidInputError):
        dice_roll_command([])
    with pytest.raises(InvalidInputError):
        dice_roll_command(["invalid"])

def test_roll_dice():
    result = roll_dice("2d6", False)
    assert len(result) == 2
    assert all(1 <= roll <= 6 for roll in result)

    result_negative = roll_dice("2d6", True)
    assert len(result_negative) == 2
    assert all(-6 <= roll <= -1 for roll in result_negative)

def test_dice_roll_command_result_range():
    num_trials = 100
    results = [dice_roll_command(["1d6"]) for _ in range(num_trials)]
    for result in results:
        assert result.isdigit()
        assert 1 <= int(result) <= 6

def test_dice_roll_command_constant():
    result = dice_roll_command(["5"])
    assert result == "5"

def test_random_command_int_range():
    for _ in range(10):
        result = int(random_command(["1", "5"]))
        assert 1 <= result <= 5
        assert isinstance(result, int)
    for _ in range(10):
        result = int(random_command(["-8", "0"]))
        assert -8 <= result <= 0
        assert isinstance(result, int)
    for _ in range(10):
        result = int(random_command(["5", "1"]))
        assert 1 <= result <= 5
        assert isinstance(result, int)

def test_random_command_float_range():
    for _ in range(10):
        result = float(random_command(["1.5", "5.5"]))
        assert 1.5 <= result <= 5.5
        assert isinstance(result, float)
    for _ in range(10):
        result = float(random_command(["5.5", "1.5"]))
        assert 1.5 <= result <= 5.5
        assert isinstance(result, float)

def test_random_command_int_and_float():
    for _ in range(10):
        result = float(random_command(["2", "5.5"]))
        assert 2 <= result <= 5.5
        assert isinstance(result, float)
    for _ in range(10):
        result = float(random_command(["5.5", "2"]))
        assert 2 <= result <= 5.5
        assert isinstance(result, float)

def test_random_command_invalid_args():
    with pytest.raises(InvalidInputError):
        random_command(["a", "5"])  # non-numeric
    with pytest.raises(InvalidInputError):
        random_command(["1"])        # too few args
    with pytest.raises(InvalidInputError):
        random_command(["1", "2", "3"])  # too many args
    with pytest.raises(InvalidInputError):
        random_command(["1.2.3", "4"])  # badly formatted float