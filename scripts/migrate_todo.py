import os
import sqlite3
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.config import config
from shared.db.db import create_dbs
from shared.models import TodoItem, orm_db


def main():
    create_dbs()

    old_db = sqlite3.connect(config.db_path)
    cursor = old_db.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'todo_list'")
    table_exists = cursor.fetchone() is not None
    if not table_exists:
        old_db.close()
        print(f"No todo_list table found in {config.db_path}. Nothing to migrate.")
        return

    cursor.execute("SELECT id, user_id, task, created_at, order_index FROM todo_list ORDER BY user_id, order_index, id")
    rows = cursor.fetchall()
    old_db.close()

    if not rows:
        print(f"No todo rows found in {config.db_path}. Nothing to migrate.")
        return

    with orm_db.atomic():
        for row in rows:
            TodoItem.insert(
                {
                    TodoItem.id: row[0],
                    TodoItem.user_id: row[1],
                    TodoItem.task: row[2],
                    TodoItem.created_at: row[3],
                    TodoItem.order_index: row[4],
                }
            ).on_conflict_ignore().execute()

    print(f"Migrated {len(rows)} todo rows from {config.db_path} to {config.db_orm_path}.")


if __name__ == "__main__":
    main()
