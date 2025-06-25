import random
from typing import Optional

import discord

responses = [
    "Without a doubt.",
    "Most likely.",
    "Yes.",
    "No.",
    "Reply hazy, try again.",
    "Ask again later.",
    "This is the way.",
    "It’s 5 o'clock somewhere, am I right?",
    "Concentrate and ask again.",
    "Better not tell you now.",
    "I've got a headache. Ask again later.",
    "U wot m8.",
    "It... wouldn't be inaccurate to assume that I couldn't exactly not say that it is or isn’t almost partially incorrect.",
    "Maybe someday.",
    "Don't count on it.",
    "My sources say no.",
    "My sources say yes.",
    "Outlook good.",
    "Outlook not so good.",
    "It’s not my job.",
    "In your dreams.",
]

f_in_chat_responses = [
    "F",
    "FFFFFFFFFFFFFFFFFFFFFF",
    "Press F to pay respects",
    ":regional_indicator_f:",
    "https://tenor.com/view/press-f-f-in-the-chat-gif-24519061",
]


async def f_in_chat(message: Optional[discord.Message] = None) -> str:
    if message:
        await message.add_reaction("🇫")
    return random.choice(f_in_chat_responses)


gg_list = [
    "Good Game!",
    "GG WP",
    "GG!",
    "https://tenor.com/view/rave-party-crazy-disco-gif-13930009",
    "https://tenor.com/view/gg-wp-good-game-well-played-ez-gif-21928504",
    "https://tenor.com/view/gg-boys-jaredfps-good-game-well-played-ggwp-gif-26211145",
    "https://tenor.com/view/multiversx-x-xportal-egld-crypto-gif-14004762323789270248",
]


def gg() -> str:
    return random.choice(gg_list)


lyrics = ["ain't nothing but a heartache", "ain't nothing but a mistake", "I never want to hear you say\nI want it that way"]


def tell_me_why():
    current_lyric = lyrics.pop(0)
    lyrics.append(current_lyric)
    return current_lyric


async def eight_ball(args: list[str], message: Optional[discord.Message] = None) -> str:
    question = " ".join(args).lower()
    match question:
        case "tell me why?" | "tell me why":
            return tell_me_why()
        case "we're no strangers to love":
            return "you know the rules and so do I"
        case "why are we still here?" | "why are we still here":
            return "just to suffer?"
        case "fuck you" | "screw you" | "f u" | "f you" | "fuck u":
            return random.choice(["No U", "Take me to dinner first.", "No."])
        case "f" | "f in the chat" | "fs in the chat":
            return await f_in_chat(message)
        case "it's dangerous to go alone" | "its dangerous to go alone":
            return random.choice(["take this\nhttps://www.youtube.com/watch?v=0m9QUoW5KnY", "take this"])  # Starbomb music video
        case "gg" | "good game":
            return gg()

    return random.choice(responses)
