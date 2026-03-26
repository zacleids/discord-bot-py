"""Peewee migrations -- 002_add_todo_table.py.

Add todo_list to the ORM database.
"""

import datetime

import peewee as pw
from peewee_migrate import Migrator


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Add the todo_list table."""

    @migrator.create_model
    class TodoItem(pw.Model):
        id = pw.AutoField()
        user_id = pw.IntegerField()
        guild_id = pw.IntegerField(null=True)  # Optional guild_id for future expansion
        task = pw.TextField()
        order_index = pw.IntegerField()
        created_at = pw.DateTimeField(default=datetime.datetime.now)
        completed_at = pw.DateTimeField(null=True)  # Optional completed_at for future expansion

        class Meta:
            table_name = "todo_list"


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Remove the todo_list table."""
    migrator.remove_model("todo_list")
