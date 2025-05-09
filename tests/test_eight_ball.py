import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from eight_ball import eight_ball, tell_me_why
from unittest.mock import AsyncMock

def test_tell_me_why():
    # First call should return the first lyric
    assert tell_me_why() == "ain't nothing but a heartache"
    # Second call should return the second lyric
    assert tell_me_why() == "ain't nothing but a mistake"
    # Third call should return the third lyric
    assert tell_me_why() == "I never want to hear you say\nI want it that way"
    # Fourth call should loop back to the first lyric
    assert tell_me_why() == "ain't nothing but a heartache"

@pytest.mark.asyncio
async def test_eight_ball_tell_me_why():
    result = await eight_ball(["tell", "me", "why?"])
    assert result in [
        "ain't nothing but a heartache",
        "ain't nothing but a mistake",
        "I never want to hear you say\nI want it that way"
    ]

@pytest.mark.asyncio
async def test_eight_ball_f_in_chat():
    mock_message = AsyncMock()
    result = await eight_ball(["f", "in", "the", "chat"], message=mock_message)
    assert result in [
        "F",
        "FFFFFFFFFFFFFFFFFFFFFF",
        "Press F to pay respects",
        ":regional_indicator_f:",
        "https://tenor.com/view/press-f-f-in-the-chat-gif-24519061"
    ]
    mock_message.add_reaction.assert_called_once_with("🇫")

@pytest.mark.asyncio
async def test_eight_ball_gg():
    result = await eight_ball(["gg"])
    assert result in [
        "Good Game!",
        "GG WP",
        "GG!",
        "https://tenor.com/view/rave-party-crazy-disco-gif-13930009",
        "https://tenor.com/view/gg-wp-good-game-well-played-ez-gif-21928504",
        "https://tenor.com/view/gg-boys-jaredfps-good-game-well-played-ggwp-gif-26211145",
        "https://tenor.com/view/multiversx-x-xportal-egld-crypto-gif-14004762323789270248"
    ]

@pytest.mark.asyncio
async def test_eight_ball_random_response():
    result = await eight_ball(["random", "question"])
    assert result in [
        'Without a doubt.',
        'Most likely.',
        'Yes.',
        'No.',
        'Reply hazy, try again.',
        'Ask again later.',
        'This is the way.',
        'It’s 5 o\'clock somewhere, am I right?',
        'Concentrate and ask again.',
        'Better not tell you now.',
        'I\'ve got a headache. Ask again later.',
        'U wot m8.',
        'It... wouldn\'t be inaccurate to assume that I couldn\'t exactly not say that it is or isn’t almost partially incorrect.',
        'Maybe someday.',
        'Don\'t count on it.',
        'My sources say no.',
        "My sources say yes.",
        'Outlook good.',
        'Outlook not so good.',
        'It’s not my job.',
        'In your dreams.'
    ]