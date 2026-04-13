"""Peewee migrations -- 005_add_live_message_table.py.

Create a reusable table for bot-controlled live-updating messages.
"""

import datetime

import peewee as pw
from peewee_migrate import Migrator


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Create the live message tracking table."""

    @migrator.create_model
    class LiveMessage(pw.Model):
        id = pw.IntegerField(primary_key=True)
        message_type = pw.CharField(max_length=255)
        message_id = pw.IntegerField(unique=True)
        channel_id = pw.IntegerField()
        guild_id = pw.IntegerField(null=True)
        user_id = pw.IntegerField()
        expires_at = pw.DateTimeField()
        last_refreshed_at = pw.DateTimeField(null=True)
        stopped_at = pw.DateTimeField(null=True)
        stop_reason = pw.CharField(max_length=255, null=True)
        created_at = pw.DateTimeField(default=datetime.datetime.now)

        class Meta:
            table_name = "livemessage"


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Drop the live message tracking table."""
    migrator.remove_model("livemessage")
