"""Peewee migrations -- 004_normalize_scope_worldclock_reminder.py.

Normalize mixed-scope data:
- worldclock: add nullable user_id, allow nullable guild_id, and delete all
  existing rows as an intentional one-time reset.
- reminder: allow nullable guild_id and normalize private reminders to
  guild_id=NULL
"""

import peewee as pw
from peewee_migrate import Migrator


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Apply worldclock/reminder scope normalization."""
    migrator.add_fields("worldclock", user_id=pw.IntegerField(null=True))
    migrator.drop_not_null("worldclock", "guild_id")
    migrator.drop_not_null("reminder", "guild_id")

    if not fake:
        # Data deletion was communicated to users in advance. This is intentional.
        # Existing worldclock rows are dropped instead of migrated.
        database.execute_sql("DELETE FROM worldclock")
        # Private reminders should not carry a guild scope.
        database.execute_sql("UPDATE reminder SET guild_id = NULL WHERE is_private = 1")


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Rollback scope normalization."""
    if not fake:
        # Worldclock data was intentionally deleted in migrate() after user comms.
        # This data loss is irreversible and cannot be recovered by rollback.
        # Restore private reminders to a non-null placeholder guild.
        database.execute_sql("UPDATE reminder SET guild_id = user_id WHERE guild_id IS NULL")
        null_reminder = database.execute_sql("SELECT COUNT(1) FROM reminder WHERE guild_id IS NULL").fetchone()[0]
        if null_reminder:
            raise RuntimeError(f"Rollback aborted: reminder NULL guild_id rows={null_reminder}")

    migrator.add_not_null("reminder", "guild_id")
    migrator.add_not_null("worldclock", "guild_id")
    migrator.remove_fields("worldclock", "user_id")
