import random
from datetime import datetime, timedelta
from typing import Dict, Tuple

FORTUNES = [
    "You will have a pleasant surprise today!",
    "A new opportunity will soon present itself.",
    "Happiness is around the corner.",
    "Be cautious of unexpected challenges.",
    "A friend will bring you good news.",
    "You will find what you seek.",
    "Today is a good day to try something new.",
    "Your hard work will soon pay off.",
    "A small act of kindness will go a long way.",
    "Luck is on your side today!",
    "You will make someone smile today.",
    "Trust your instincts.",
    "Adventure awaits you.",
    "You will learn something valuable today.",
    "A pleasant surprise is in store for you.",
    "You will overcome a challenge with ease.",
    "Someone appreciates you more than you know.",
    "A new friendship is on the horizon.",
    "You will discover a hidden talent.",
    "Good fortune will find you soon.",
    "You will go to sleep and wake up tomorrow.",
    "You will have a moment of déjà vu.",
    "You will have an awkward encounter with a stranger.",
    "You will accidentally send a text to the wrong person.",
    # Silly fortunes
    "You will step on a LEGO today. Beware.",
    "A duck will judge you silently from afar.",
    "You will find a sock with no match.",
    "Your next yawn will be contagious.",
    "Beware of squirrels plotting in the park.",
    "You will forget why you walked into a room.",
    "A potato will cross your path.",
    "You will sneeze exactly three times in a row.",
    "You will win an imaginary argument today.",
    "Your left shoe will feel slightly tighter than your right.",
    "Error 404: Fortune not found.",
    "You will trip over an invisible obstacle.",
    "A cloud will look like a dinosaur today.",
    "You will have a conversation with a houseplant.",
    "A fortune cookie will be jealous of you.",
    "A cat will stare at you with judgment.",
    "You will have a dream about cheese.",
    "You will be serenaded by a bird today.",
    "You will have a craving for something unusual.",    
    #Snarky fortunes
    "What do I look like, a fortune teller!",
    "Your shampoo dosent always like your concerts.",
    "Your lucky number is 42, but only on Tuesdays.",
    "Your lucky numbers today are 3 and uhhh... 7?",
    "You can do anything you set your mind to or whatever.",
    "Never trust a fortune cookie.",
    "Never bite the hand that fingers you.",
    "The Moon is in pisces I think, so that probably means you're lucky or something."
    "tell me why, aint nothing but a heart ache- wtf!? im showering is privacy too much to ask?"
    "you know the rules and so do I!",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ", #Rickroll link
    "You will be Rickrolled today.",
    ]

# Tracks (user_id, date) -> count
_fortune_counter: Dict[Tuple[int, str], int] = {}

SNARKY_LINES = [
    "Believe it or not, your fortune is still...",
    "I don't know why you're asking again, but here it is:",
    "You really want to hear this again? Fine:",
    "Oh yea, just ask {num} times, I'm sure that'll change it:",
    "Still hoping for a different answer? Here it is:",
    "Persistence is key, but your fortune hasn't changed:",
    "Trying to break the bot? Nope, same fortune:",
    "You must really want a new fortune. Too bad!",
    "Spoiler: It's the same as before:",
    "You know, asking again won't change the outcome:",
    "You must be bored. Here's your fortune again:",
    "You've already asked {num} times, but here it is again:",
]

def get_fortune(user_id: int, date: str = None) -> str:
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    key = (user_id, date)
    count = _fortune_counter.get(key, 0) + 1
    _fortune_counter[key] = count
    # Clean up old counters (optional, but keeps memory low)
    for k in list(_fortune_counter.keys()):
        if k[1] != date:
            del _fortune_counter[k]
    fortune = _get_deterministic_fortune(user_id, date)
    if count > 1:
        snark = random.choice(SNARKY_LINES).replace("{num}", str(count))
        return f"{snark}\n{fortune}"
    return fortune

def _get_deterministic_fortune(user_id: int, date: str) -> str:
    seed_str = f"{user_id}-{date}"
    rng = random.Random(seed_str)
    fortune = rng.choice(FORTUNES)

    # Check yesterday's fortune
    yesterday = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_seed_str = f"{user_id}-{yesterday}"
    yesterday_rng = random.Random(yesterday_seed_str)
    yesterday_fortune = yesterday_rng.choice(FORTUNES)

    # If today's fortune matches yesterday's, adjust the seed
    if fortune == yesterday_fortune:
        seed_str += "1"
        rng = random.Random(seed_str)
        fortune = rng.choice(FORTUNES)

    return fortune
