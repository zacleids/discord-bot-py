import os

from shared.log import get_ray_id, log_event

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
    log_event(
        "DB_READY",
        {"event": "DB_READY", "db_path": config.db_path, "db_orm_path": config.db_orm_path, "ray_id": get_ray_id()},
        level="info",
    )
