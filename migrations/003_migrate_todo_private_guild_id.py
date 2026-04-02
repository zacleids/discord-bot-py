"""Peewee migrations -- 003_migrate_todo_private_guild_id.py.

Standardize private todo items to use guild_id=NULL (DM/private) instead of
the previous sentinel value of 0.
"""

import peewee as pw
from peewee_migrate import Migrator


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Migrate private todo items from guild_id=0 to guild_id=NULL."""
    if not fake:
        database.execute_sql("UPDATE todo_list SET guild_id = NULL WHERE guild_id = 0")


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Revert private todo items from guild_id=NULL back to guild_id=0."""
    if not fake:
        database.execute_sql("UPDATE todo_list SET guild_id = 0 WHERE guild_id IS NULL")
