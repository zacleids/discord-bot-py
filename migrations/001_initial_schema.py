"""Peewee migrations -- 001_initial_schema.py.

Initial migration: creates all tables for the current database schema.
"""

import datetime
from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator

with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Create all tables for the initial schema."""

    @migrator.create_model
    class CurrencyRate(pw.Model):
        base_currency = pw.CharField(max_length=255)
        rates_json = pw.TextField()
        last_updated = pw.TimestampField(default=datetime.datetime.now)

        class Meta:
            table_name = "currencyrate"

    @migrator.create_model
    class DailyChecklist(pw.Model):
        user_id = pw.IntegerField()
        item = pw.CharField(max_length=255)
        sort_order = pw.IntegerField(constraints=[pw.SQL("DEFAULT 0")])
        deleted_at = pw.DateTimeField(null=True)
        created_at = pw.DateTimeField(default=datetime.datetime.now)

        class Meta:
            table_name = "dailychecklist"

    @migrator.create_model
    class DailyChecklistCheck(pw.Model):
        checklist_item = pw.ForeignKeyField(DailyChecklist, column_name="checklist_item_id", backref="checks")
        checked_at = pw.DateField()

        class Meta:
            table_name = "dailychecklistcheck"
            indexes = ((("checklist_item", "checked_at"), True),)

    @migrator.create_model
    class HangmanGame(pw.Model):
        id = pw.IntegerField(primary_key=True)
        guild_id = pw.IntegerField()
        user_id = pw.IntegerField()
        phrase = pw.TextField()
        guessed_characters = pw.TextField(default="")
        num_guesses = pw.IntegerField(null=True)
        game_over = pw.BooleanField(default=False)
        board = pw.TextField(default="")
        created_at = pw.TimestampField(default=datetime.datetime.now)

        class Meta:
            table_name = "hangmangame"

    @migrator.create_model
    class Reminder(pw.Model):
        id = pw.IntegerField(primary_key=True)
        user_id = pw.IntegerField()
        guild_id = pw.IntegerField()
        channel_id = pw.IntegerField()
        message = pw.TextField()
        is_private = pw.BooleanField(default=False)
        remind_at = pw.TimestampField()
        created_at = pw.DateTimeField(default=datetime.datetime.now)

        class Meta:
            table_name = "reminder"

    @migrator.create_model
    class WorldClock(pw.Model):
        guild_id = pw.IntegerField()
        timezone_str = pw.CharField(max_length=255)
        label = pw.CharField(max_length=255, null=True)
        created_at = pw.DateTimeField(default=datetime.datetime.now)

        class Meta:
            table_name = "worldclock"


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Drop all tables created in this migration."""
    migrator.remove_model("dailychecklistcheck")
    migrator.remove_model("dailychecklist")
    migrator.remove_model("currencyrate")
    migrator.remove_model("hangmangame")
    migrator.remove_model("reminder")
    migrator.remove_model("worldclock")
