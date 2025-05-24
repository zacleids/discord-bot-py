from peewee import *
import datetime
from config import Config

config = Config()

orm_db = SqliteDatabase(config.db_orm_path)

class BaseModel(Model):
    class Meta:
        database = orm_db

class CurrencyRate(BaseModel):
    base_currency = CharField()
    rates_json = TextField()  # Store rates as JSON string
    last_updated = TimestampField(default=datetime.datetime.now)

class DailyChecklist(BaseModel):
    user_id = IntegerField()
    item = CharField()
    sort_order = IntegerField(constraints=[SQL('DEFAULT 0')])
    deleted_at = DateTimeField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

class DailyChecklistCheck(BaseModel):
    checklist_item = ForeignKeyField(DailyChecklist, backref='checks')
    checked_at = DateField()
    class Meta:
        indexes = (
            (('checklist_item', 'checked_at'), True),
        )

class HangmanGame(BaseModel):
    id = IntegerField(primary_key=True)
    guild_id = IntegerField()
    user_id = IntegerField()
    phrase = TextField()
    guessed_characters = TextField(default="")
    num_guesses = IntegerField(null=True)
    game_over = BooleanField(default=False)
    board = TextField(default="")
    created_at = TimestampField(default=datetime.datetime.now)

class Reminder(BaseModel):
    id = IntegerField(primary_key=True)
    user_id = IntegerField()
    guild_id = IntegerField()
    channel_id = IntegerField()
    message = TextField()
    is_private = BooleanField(default=False)
    remind_at = TimestampField()
    created_at = DateTimeField(default=datetime.datetime.now)

class WorldClock(BaseModel):
    guild_id = IntegerField()
    timezone_str = CharField()
    label = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
