import os

from .. import todo
from ..config import config
from ..models import (
    CurrencyRate,
    DailyChecklist,
    DailyChecklistCheck,
    HangmanGame,
    Reminder,
    WorldClock,
    orm_db,
)


def create_dbs():
    todo.create_db()

    # Ensure DB file exists
    if not os.path.exists(config.db_orm_path):
        open(config.db_orm_path, "a").close()
        print("DB Created!")
    else:
        print("DB already exists")

    print(f"Connecting to DB: {config.db_orm_path}")
    orm_db.connect()
    orm_db.create_tables([HangmanGame, Reminder, WorldClock, DailyChecklist, DailyChecklistCheck, CurrencyRate])
