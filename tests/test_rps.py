import pytest
from rps import play_rock_paper_scissors, RPSChoice
from errors import InvalidInputError


def test_play_rock_paper_scissors_valid_choices():
    for choice in ["rock", "paper", "scissors"]:
        result = play_rock_paper_scissors([choice])
        assert any(keyword in result for keyword in ["You win!", "You lose!", "It's a tie!"])


def test_play_rock_paper_scissors_invalid_choice():
    with pytest.raises(InvalidInputError):
        play_rock_paper_scissors([])

    result = play_rock_paper_scissors(["invalid_choice"])
    assert result in [
        "I dont know what you're trying to pull",
        "I didnt know we were playing Rock, Paper, Scissors, and invalid_choice. How do you play?",
        "That is neither rock, nor paper, nor scissors",
    ]
