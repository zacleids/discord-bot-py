import sys
import os
import pytest

from coin import flip_coin, flip_coins
from errors import InvalidInputError


sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # This line is necessary to import the module from the parent directory


# Test flip_coin returns one of the expected results
def test_flip_coin_result():
    result = flip_coin()
    assert result in ["heads", "tails", "Wow, it landed on its edge! Weird right?"]


# Test flip_coins with valid single coin
def test_flip_coins_one():
    result = flip_coins(["1"])
    assert result in ["heads", "tails", "Wow, it landed on its edge! Weird right?"]


# Test flip_coins with <25 coins returns string of H/T
@pytest.mark.parametrize("n", [2, 5, 10, 24])
def test_flip_coins_small_number(n):
    result = flip_coins([str(n)])
    assert len(result) == n
    assert set(result).issubset({"H", "T"})


# Test flip_coins with >=25 coins returns summary
@pytest.mark.parametrize("n", [25, 50, 100, 1000])
def test_flip_coins_large_number(n):
    result = flip_coins([str(n)])
    assert result.startswith("Heads: ")
    assert "Tails: " in result


# Test flip_coins with invalid argument count
@pytest.mark.parametrize("args", [[], ["1", "2"]])
def test_flip_coins_invalid_arg_count(args):
    with pytest.raises(InvalidInputError):
        flip_coins(args)


# Test flip_coins with non-integer input
def test_flip_coins_non_integer():
    with pytest.raises(InvalidInputError):
        flip_coins(["abc"])


# Test flip_coins with out-of-range values
@pytest.mark.parametrize("val", ["0", "-1", "100001"])
def test_flip_coins_out_of_range(val):
    with pytest.raises(InvalidInputError):
        flip_coins([val])
