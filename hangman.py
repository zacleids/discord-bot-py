import random
import re
from datetime import datetime

import emoji
from peewee import *

from db.db import orm_db


class BaseModel(Model):
    class Meta:
        database = orm_db


class HangmanGame(BaseModel):
    id = IntegerField(primary_key=True)
    guild_id = IntegerField()
    user_id = IntegerField()
    phrase = TextField()
    guessed_characters = TextField(default="")  # Stores guessed letters as a string
    num_guesses = IntegerField(null=True)  # None = Unlimited guesses
    game_over = BooleanField(default=False)
    board = TextField(default="")  # Stores the current display board state
    created_at = TimestampField(default=datetime.now)

    def calculate_board(self):
        """Updates the board state and tracks guesses."""
        pass_through_chars = {" ", "?", "!", "'", "\"", ".", ",", "<", ">",
                              "=", "-", "+", "*", "/", ":", ";", "(", ")",
                              "{", "}", "[", "]", "|", "@", "#", "$", "%",
                              "^", "&", "`", "~"}
        guessed_set = set(self.guessed_characters)
        pass_through_chars.update(guessed_set)

        # Build the board representation. Use a \ before the underscore to prevent discord Markdown formatting
        self.board = "".join(char if char.lower() in pass_through_chars else r"\_" for char in self.phrase)

        # Track incorrect guesses
        incorrect_guesses = sorted(guess for guess in guessed_set if guess not in self.phrase)

        # Check win/loss conditions
        if "_" not in self.board:
            self.game_over = True  # Player won
        elif self.num_guesses is not None and len(incorrect_guesses) >= self.num_guesses:
            self.game_over = True  # Player lost

        self.save()  # Save the updated board and game status

    def print_board(self) -> str:
        """Returns the current board state with guess info."""
        extra_str = ''
        incorrect_guesses = [guess for guess in self.guessed_characters if guess not in self.phrase]

        if incorrect_guesses:
            extra_str += f"\nIncorrect guesses: {', '.join(incorrect_guesses)}"

        if self.num_guesses is not None:  # Show remaining guesses only if limited
            remaining_guesses = self.num_guesses - len(incorrect_guesses)
            extra_str += f"\n{remaining_guesses}/{self.num_guesses} guesses remaining"
            if remaining_guesses <= 0:
                extra_str += f"\n**You Lose!** :regional_indicator_f:\nPhrase: {self.phrase}"

        if "_" not in self.board and "Lose" not in extra_str:
            extra_str += "\n**You Win!!!** 🎉"
            if len(incorrect_guesses) == 0:
                perfect_game_congrats = [
                    "Amazing, a perfect game!",
                    "Wow, not a single letter guessed wrong!",
                    "You nailed it, a perfect game!",
                    "Great job not missing even once."
                ]
                extra_str += f"\n{random.choice(perfect_game_congrats)}"


        return f"{self.board}{extra_str}"

    def guess_new_letters(self, new_guesses: str):
        new_guesses = new_guesses.lower()
        """Adds new guessed letters, updates the board, and checks win conditions."""
        new_guessed_set = set(self.guessed_characters) | set(new_guesses)
        new_guessed_set.discard(" ")
        self.guessed_characters = "".join(sorted(new_guessed_set))  # Keep guesses sorted
        self.calculate_board()  # Update the board and save changes


EIGHT_HOURS = 8 * 60 * 60


def get_active_hangman_game(guild_id: int) -> HangmanGame | None:
    now = int(datetime.now().timestamp())
    try:
        query = (HangmanGame
                 .select()
                 .where((HangmanGame.guild_id == guild_id) &
                        (HangmanGame.game_over == False) &
                        (HangmanGame.created_at > (now - EIGHT_HOURS)))
                 .order_by(HangmanGame.created_at.desc())
                 .get()
                 )
        # WHERE guild_id = ?
        # AND game_over = 0
        # AND datetime(created_at) >= datetime('now', '-8 hours')""", (guild_id,))
    except:
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
