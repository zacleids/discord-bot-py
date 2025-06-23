import os
import sqlite3

from db.db import create_dbs, orm_db
from time_funcs import WorldClock

# Get the absolute path of the db file relative to the script's location
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "../db/bot.db")

# Connect to the old database
old_db = sqlite3.connect(db_path)
cursor = old_db.cursor()

# Fetch all entries from the old world_clock table
cursor.execute("SELECT guild_id, timezone_str, label, created_at FROM world_clock")
entries = cursor.fetchall()

create_dbs()
# Insert entries into the new world_clock table
with orm_db.atomic():
    for entry in entries:
        WorldClock.create(guild_id=entry[0], timezone_str=entry[1], label=entry[2], created_at=entry[3])
orm_db.close()

print("Migration completed successfully.")
