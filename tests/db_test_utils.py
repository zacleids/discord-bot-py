# db_test_utils.py
# Utility functions for database testing with Peewee
from peewee import Model


def wipe_table(table: Model):
    print(f"Wiping table: {table.__name__}")
    """Delete all rows from the given Peewee table."""
    table.delete().execute()
