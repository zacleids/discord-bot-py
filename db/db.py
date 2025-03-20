import os
from peewee import SqliteDatabase

# Get the absolute path to ensure it works no matter where the script runs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "bot_orm.db")   # Ensures it's in `db/`

orm_db = SqliteDatabase(DB_NAME)


import time_funcs
import todo
from hangman import HangmanGame, orm_db
from reminder import Reminder
from time_funcs import WorldClock


def create_dbs():
    todo.create_db()

    orm_db_file_path = "bot_orm.db"

    # Ensure DB file exists
    if not os.path.exists(DB_NAME):
        open(DB_NAME, 'a').close()
        print("DB Created!")
    else:
        print("DB already exists")

    orm_db.connect()
    orm_db.create_tables([HangmanGame, Reminder, WorldClock])
