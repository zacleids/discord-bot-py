import json
import random
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pytz import timezone, all_timezones

import db.db
import hangman
from reminder import Reminder
import time_funcs
import todo

import utils
from color import generate_image
from dice import dice_roll_command
from errors import InvalidInputError


phrase = "you're a cute kitty!"
guessed_letters = "hgtofijk"
# board, c, i = hangman.calculate_board(phrase, guessed_letters)
# print(board)
# print(len(c))
# print(i)
# res = hangman.print_board(board, c, i, 5)
# print(res)

# hg = hangman.HangmanGameManual((0, 0, 0, phrase, guessed_letters, 5, 0, datetime.now()))
# print(hg.print_board())
#
# hg.guess_new_letters("yura")
# print(hg.print_board())

# db.db.create_dbs()

# hg = hangman.HangmanGame.create(guild_id=1322792221665132567, user_id=10, phrase=phrase, num_guesses=10)
#
# print(hg.print_board())
#
# hg.calculate_board()
# # print(hg.board)
# print(hg.print_board())

# print()
# hg.guess_new_letters("ykt")
# print(hg.print_board())
#
# print()
# hg.guess_new_letters(guessed_letters)
# print(hg.print_board())
#
#
# print()
# hg.guess_new_letters("ureac")
# print(hg.print_board())

# hg.save()

# query = hangman.HangmanGame.select().where(hangman.HangmanGame.guild_id == 0).order_by(hangman.HangmanGame.created_at.desc())
# print(query)
# for hg in query:
#     print(hg.phrase, hg.num_guesses)

# now = datetime.now()
# reminders = Reminder.select().where(Reminder.remind_at <= now)
# for reminder in reminders:
#     print(reminder.message, reminder.remind_at)
# print(1740988677 - hangman.EIGHT_HOURS)
# print(datetime.fromtimestamp(1740988677))
# now = int(datetime.now().timestamp())
# print(now)
# print(int(now))
# print(now - hangman.EIGHT_HOURS)

# print(1741494178 - hangman.EIGHT_HOURS)

# def dump(obj):
#     for attr in dir(obj):
#         print("obj.%s = %r" % (attr, getattr(obj, attr)))
#
#
# q = hangman.get_active_hangman_game(1322792221665132567)
# # print(f"q: {q}")
# print(dump(q))
# q.calculate_board()
# print(q.print_board())

# hg = hangman.get_active_hangman_game(1322792221665132567)

# print(type(hg.created_at))
# print(hg.created_at)
# time_change = timedelta(hours=8)
# new_time = hg.created_at + time_change
# print(new_time)
# print(new_time.timestamp())
# print(int(new_time.timestamp()))
# print(hg.created_at + hangman.EIGHT_HOURS)

tzs = time_funcs.list_timezones(1322792221665132567)
print(tzs)
print(time_funcs.format_tzs_response_str(tzs))