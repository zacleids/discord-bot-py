import pytest
import time
from hangman import validate_chars, HangmanGame, get_active_hangman_game
from tests.db_test_utils import wipe_table


def test_validate_chars_positive():
    # Single word
    valid, msg = validate_chars("hello")
    assert valid
    # Normal phrase
    valid, msg = validate_chars("hello world")
    assert valid
    # Phrase with lots of punctuation and allowed ASCII
    valid, msg = validate_chars("Hello, world! How's it going? @user #hashtag $100% ^&*()_+-=;:'\"[]{}|<>,./~`")
    assert valid


def test_validate_chars_unicode_emoji():
    # Unicode emoji
    valid, msg = validate_chars("hello 😊")
    assert not valid
    assert "non-ascii characters" in msg.lower()


def test_validate_chars_evil_unicode_space():
    # Evil unicode space (U+200B zero-width space)
    valid, msg = validate_chars("hello\u200bworld")
    assert not valid
    assert "non-ascii" in msg.lower()


def test_validate_chars_custom_discord_emoji():
    # Custom Discord emoji
    valid, msg = validate_chars("hello <:custom_emoji:1234567890>")
    assert not valid
    assert "custom emojis" in msg.lower()


def test_validate_chars_unicode_punctuation():
    # Unicode punctuation (em dash)
    valid, msg = validate_chars("hello — world")
    assert not valid
    assert "non-ascii" in msg.lower()


@pytest.fixture(autouse=True)
def clear_hangman_table():
    # Clear the HangmanGame table before each test
    wipe_table(HangmanGame)


GUILD_ID = 1
USER_ID = 1


def test_calculate_board_and_guess_new_letters():
    # Create a new game with a phrase
    phrase = "hello world!"
    game = HangmanGame.create(guild_id=GUILD_ID, user_id=USER_ID, phrase=phrase, num_guesses=6)
    # Initial board: nothing guessed
    game.calculate_board()
    board = game.print_board()
    # All letters should be hidden (except allowed chars)
    assert r"\_\_\_\_\_ \_\_\_\_\_!" in board
    # Guess 'h', 'e', 'l'
    game.guess_new_letters("hel")
    board = game.print_board()
    assert "h" in board and "e" in board and board.count("l") == 3
    # Guess 'o', 'w', 'r', 'd'
    game.guess_new_letters("owrd")
    board = game.print_board()
    # All letters should be revealed
    assert "hello world!" in board
    assert "**You Win!!!**" in board
    # Guess a wrong letter
    game = HangmanGame.create(guild_id=GUILD_ID, user_id=USER_ID, phrase="abc", num_guesses=1)
    game.guess_new_letters("z")
    board = game.print_board()
    assert "z" in board
    assert "0/1 guesses remaining" in board
    assert "**You Lose!**" in board


def test_perfect_game_congrats_message():
    # Test that a perfect game triggers a congrats message
    phrase = "abc"
    game = HangmanGame.create(guild_id=GUILD_ID, user_id=USER_ID, phrase=phrase, num_guesses=10)
    # Guess all correct letters, no incorrect guesses
    game.guess_new_letters("abc")
    board = game.print_board()
    # Check for win message
    assert "**You Win!!!**" in board
    # Check for one of the perfect game congrats messages
    congrats_options = [
        "Amazing, a perfect game!",
        "Wow, not a single letter guessed wrong!",
        "You nailed it, a perfect game!",
        "Great job not missing even once.",
    ]
    assert any(msg in board for msg in congrats_options)


def test_incorrect_guesses_display():
    # Test that incorrect guesses are displayed correctly
    phrase = "hangman"
    game = HangmanGame.create(guild_id=GUILD_ID, user_id=USER_ID, phrase=phrase, num_guesses=5)
    game.guess_new_letters("z")
    board = game.print_board()
    assert "Incorrect guesses: z" in board
    # Add another incorrect guess
    game.guess_new_letters("q")
    board = game.print_board()
    assert "Incorrect guesses: q, z" in board or "Incorrect guesses: z, q" in board


def test_guessing_same_letter_does_not_increase_count():
    # Test that guessing the same incorrect letter doesn't increase guess count
    phrase = "hangman"
    game = HangmanGame.create(guild_id=GUILD_ID, user_id=USER_ID, phrase=phrase, num_guesses=5)
    game.guess_new_letters("z")
    board = game.print_board()
    assert "4/5 guesses remaining" in board
    # Guess 'z' again
    game.guess_new_letters("z")
    board = game.print_board()
    assert "4/5 guesses remaining" in board
    # Now test with a correct letter
    game.guess_new_letters("h")
    board = game.print_board()
    assert "4/5 guesses remaining" in board
    # Guess 'h' again
    game.guess_new_letters("h")
    board = game.print_board()
    assert "4/5 guesses remaining" in board


def test_get_active_hangman_game_positive():
    # Create an active game within the last 8 hours
    now = int(time.time())
    game = HangmanGame.create(guild_id=GUILD_ID, user_id=USER_ID, phrase="test", num_guesses=5, created_at=now, game_over=False)
    found = get_active_hangman_game(GUILD_ID)
    assert found is not None
    assert found.id == game.id
    assert found.guild_id == 1
    assert not found.game_over


def test_get_active_hangman_game_negative():
    # No game for this guild
    empty_guild_id = 11
    found = get_active_hangman_game(empty_guild_id)
    assert found is None
    # Game is too old
    old_guild_id = 22
    old_time = int(time.time()) - (9 * 60 * 60)  # 9 hours ago
    HangmanGame.create(guild_id=old_guild_id, user_id=USER_ID, phrase="old", num_guesses=5, created_at=old_time, game_over=False)
    found = get_active_hangman_game(old_guild_id)
    assert found is None
    # Game is over
    over_guild_id = 33
    recent_time = int(time.time())
    HangmanGame.create(guild_id=over_guild_id, user_id=USER_ID, phrase="over", num_guesses=5, created_at=recent_time, game_over=True)
    found = get_active_hangman_game(over_guild_id)
    assert found is None


def test_phrase_with_only_punctuation_or_spaces():
    game = HangmanGame.create(guild_id=GUILD_ID, user_id=USER_ID, phrase="!!! ???", num_guesses=5)
    game.calculate_board()
    board = game.print_board()
    assert "!!! ???" in board
    assert "You Win" in board


def test_guessing_non_letter_characters():
    game = HangmanGame.create(guild_id=GUILD_ID, user_id=USER_ID, phrase="abc!", num_guesses=5)
    game.guess_new_letters("!")
    board = game.print_board()
    # Should not count as incorrect guess
    assert "5/5 guesses remaining" in board
    # Should not reveal any letters
    assert r"\_\_\_!" in board


def test_empty_phrase_immediate_win():
    game = HangmanGame.create(guild_id=GUILD_ID, user_id=USER_ID, phrase="", num_guesses=5)
    game.calculate_board()
    board = game.print_board()
    assert "You Win" in board


def test_unlimited_guesses_never_lose():
    game = HangmanGame.create(guild_id=GUILD_ID, user_id=USER_ID, phrase="abc", num_guesses=None)
    for _ in range(20):
        game.guess_new_letters("z")
    board = game.print_board()
    assert "You Lose" not in board


def test_case_insensitivity():
    game = HangmanGame.create(guild_id=GUILD_ID, user_id=USER_ID, phrase="AbC", num_guesses=5)
    game.guess_new_letters("a")
    board = game.print_board()
    assert "A" in board or "a" in board
    game.guess_new_letters("B")
    board = game.print_board()
    assert "B" in board or "b" in board
    game.guess_new_letters("c")
    board = game.print_board()
    assert "You Win" in board


def test_guessing_after_game_over():
    game = HangmanGame.create(guild_id=GUILD_ID, user_id=USER_ID, phrase="abc", num_guesses=1)
    game.guess_new_letters("z")  # Lose
    board_before = game.print_board()
    game.guess_new_letters("a")
    board_after = game.print_board()
    # Board and state should not change after game over
    assert board_before == board_after


def test_case_in_phrase_is_preserved():
    # Phrase has mixed case, guesses are lowercase
    phrase = "PyThOn"
    game = HangmanGame.create(guild_id=GUILD_ID, user_id=USER_ID, phrase=phrase, num_guesses=6)
    # Guess all letters in lowercase
    for letter in "python":
        game.guess_new_letters(letter)
    board = game.print_board()
    # The board should reveal the original case of the phrase
    assert "PyThOn" in board
    assert "You Win" in board
