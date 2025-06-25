import random
from enum import Enum

from .errors import InvalidInputError


class RPSChoice(Enum):
    Rock = "rock"
    Paper = "paper"
    Scissors = "scissors"


def print_win_str(bot_choice: RPSChoice, player_choice: RPSChoice) -> str:
    if player_choice == bot_choice:
        result = "It's a tie!"
    elif (
        (player_choice == RPSChoice.Rock and bot_choice == RPSChoice.Scissors)
        or (player_choice == RPSChoice.Paper and bot_choice == RPSChoice.Rock)
        or (player_choice == RPSChoice.Scissors and bot_choice == RPSChoice.Paper)
    ):
        result = "You win!"
    else:
        result = "You lose!"

    return f"You chose **{player_choice.value}**. I chose **{bot_choice.value}**.\n**{result}**"


def play_rock_paper_scissors(args: list[str]) -> str:
    if len(args) == 0:
        raise InvalidInputError("Invalid input. please use choose rock, paper, or scissors")

    player_choice_str = " ".join(args).lower()

    # Convert string to Enum member
    try:
        player_choice = RPSChoice(player_choice_str)

        if player_choice in RPSChoice:
            bot_choice = random.choice(list(RPSChoice))
            return print_win_str(bot_choice, player_choice)
    except ValueError:
        return random.choice(
            [
                "I dont know what you're trying to pull",
                f"I didnt know we were playing Rock, Paper, Scissors, and {player_choice_str}. How do you play?",
                "That is neither rock, nor paper, nor scissors",
            ]
        )
