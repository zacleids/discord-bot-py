"""Peewee migrations -- 006_make_live_message_expires_at_nullable.py.

Allow live messages to refresh indefinitely by making expires_at nullable.
"""

import peewee as pw
from peewee_migrate import Migrator


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Allow livemessage.expires_at to be NULL."""
    migrator.drop_not_null("livemessage", "expires_at")


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Restore livemessage.expires_at to NOT NULL."""
    if not fake:
        null_count = database.execute_sql("SELECT COUNT(1) FROM livemessage WHERE expires_at IS NULL").fetchone()[0]
        if null_count:
            raise RuntimeError(f"Rollback aborted: livemessage NULL expires_at rows={null_count}")

    migrator.add_not_null("livemessage", "expires_at")
