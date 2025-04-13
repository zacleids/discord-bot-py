import os
from peewee import SqliteDatabase
from config import Config

config = Config()
orm_db = SqliteDatabase(config.db_orm_path)

import time_funcs
import todo
from hangman import HangmanGame, orm_db
from reminder import Reminder
from time_funcs import WorldClock
from daily_checklist import DailyChecklist, DailyChecklistCheck


def create_dbs():
    todo.create_db()

    # Ensure DB file exists
    if not os.path.exists(config.db_orm_path):
        open(config.db_orm_path, 'a').close()
        print("DB Created!")
    else:
        print("DB already exists")

    orm_db.connect()
    orm_db.create_tables([HangmanGame, Reminder, WorldClock, DailyChecklist, DailyChecklistCheck])
