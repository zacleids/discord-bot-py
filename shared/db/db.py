import os
from pathlib import Path

import peewee as pw
from peewee_migrate import Router

from shared.log import get_ray_id, log_event

from ..config import config
from ..models import orm_db

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MIGRATE_DIR = PROJECT_ROOT / "migrations"


def run_migrations(database: pw.Database):
    """Run all pending peewee-migrate migrations."""
    router = Router(database, migrate_dir=str(MIGRATE_DIR))
    router.run()


def create_dbs():
    # Ensure DB file exists
    if not os.path.exists(config.db_orm_path):
        open(config.db_orm_path, "a").close()
        print("DB Created!")
    else:
        print("DB already exists")

    print(f"Connecting to DB: {config.db_orm_path}")
    orm_db.connect(reuse_if_open=True)
    run_migrations(orm_db)
    log_event(
        "DB_READY",
        {"event": "DB_READY", "db_path": config.db_path, "db_orm_path": config.db_orm_path, "ray_id": get_ray_id()},
        level="info",
    )
