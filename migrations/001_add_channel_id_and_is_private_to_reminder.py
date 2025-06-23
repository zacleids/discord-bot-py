from pathlib import Path

import peewee as pw
from playhouse.migrate import SqliteMigrator, migrate

# Construct the database path using pathlib with a relative path
db_path = Path(__file__).resolve().parent.parent / "db" / "bot_orm.db"
db = pw.SqliteDatabase(db_path)
migrator = SqliteMigrator(db)

channel_id_field = pw.IntegerField(null=True)
is_private_field = pw.BooleanField(default=False)

with db.atomic():
    print("Starting migration...")
    migrate(
        migrator.add_column("reminder", "channel_id", channel_id_field),
        migrator.add_column("reminder", "is_private", is_private_field),
    )
    print("Migration completed.")
