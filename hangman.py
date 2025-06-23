from models import HangmanGame
import random
import re
from datetime import datetime
import emoji

EIGHT_HOURS = 8 * 60 * 60


def get_active_hangman_game(guild_id: int) -> HangmanGame | None:
    now = int(datetime.now().timestamp())
    try:
        query = (
            HangmanGame.select()
            .where(
                (HangmanGame.guild_id == guild_id)
                & (HangmanGame.game_over == False)  # noqa: E712
                & (HangmanGame.created_at > (now - EIGHT_HOURS))
            )
            .order_by(HangmanGame.created_at.desc())
            .get()
        )
        # WHERE guild_id = ?
        # AND game_over = 0
        # AND datetime(created_at) >= datetime('now', '-8 hours')""", (guild_id,))
    except HangmanGame.DoesNotExist:
        return None

    # print(f"querry: {query}")
    return query


def validate_chars(chars: str) -> tuple[bool, str]:
    # Check for non-ASCII characters
    if not all(ord(char) < 128 for char in chars):
        return False, "Your phrase contains non-ASCII characters. Only basic English letters and punctuation are allowed."

    # Check for custom emojis using regex
    custom_emoji_pattern = r"<a?:\w+:\d+>"
    if re.search(custom_emoji_pattern, chars):
        return False, "Custom emojis are not allowed in the hangman phrase."

    # Check for Unicode emojis
    if any(char in chars for char in emoji.EMOJI_DATA):
        return False, "Unicode emojis are not allowed in the hangman phrase."

    return True, ""


def calculate_board(game: HangmanGame):
    pass_through_chars = {
        " ",
        "?",
        "!",
        "'",
        '"',
        ".",
        ",",
        "<",
        ">",
        "=",
        "-",
        "+",
        "*",
        "/",
        ":",
        ";",
        "(",
        ")",
        "{",
        "}",
        "[",
        "]",
        "|",
        "@",
        "#",
        "$",
        "%",
        "^",
        "&",
        "`",
        "~",
    }
    guessed_set = set(game.guessed_characters)
    pass_through_chars.update(guessed_set)
    game.board = "".join(char if char.lower() in pass_through_chars else r"\_" for char in game.phrase)
    incorrect_guesses = sorted(guess for guess in guessed_set if guess not in game.phrase)
    if "_" not in game.board:
        game.game_over = True
    elif game.num_guesses is not None and len(incorrect_guesses) >= game.num_guesses:
        game.game_over = True
    game.save()


def print_board(game: HangmanGame) -> str:
    extra_str = ""
    incorrect_guesses = [guess for guess in game.guessed_characters if guess not in game.phrase]
    if incorrect_guesses:
        extra_str += f"\nIncorrect guesses: {', '.join(incorrect_guesses)}"
    if game.num_guesses is not None:
        remaining_guesses = game.num_guesses - len(incorrect_guesses)
        extra_str += f"\n{remaining_guesses}/{game.num_guesses} guesses remaining"
        if remaining_guesses <= 0:
            extra_str += f"\n**You Lose!** :regional_indicator_f:\nPhrase: {game.phrase}"
    if "_" not in game.board and "Lose" not in extra_str:
        extra_str += "\n**You Win!!!** 🎉"
        if len(incorrect_guesses) == 0:
            perfect_game_congrats = [
                "Amazing, a perfect game!",
                "Wow, not a single letter guessed wrong!",
                "You nailed it, a perfect game!",
                "Great job not missing even once.",
            ]
            extra_str += f"\n{random.choice(perfect_game_congrats)}"
    return f"{game.board}{extra_str}"


def guess_new_letters(game: HangmanGame, new_guesses: str):
    if not game or game.game_over:
        return
    new_guesses = new_guesses.lower()
    new_guessed_set = set(game.guessed_characters) | set(new_guesses)
    new_guessed_set.discard(" ")
    game.guessed_characters = "".join(sorted(new_guessed_set))
    calculate_board(game)


# patch onto HangmanGame to call them as methods.
HangmanGame.calculate_board = calculate_board
HangmanGame.print_board = print_board
HangmanGame.guess_new_letters = guess_new_letters
