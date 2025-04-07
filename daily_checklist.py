import datetime
import pytz
from peewee import Model, IntegerField, CharField, DateField
from db.db import orm_db
from typing import Tuple, List

class DailyChecklist(Model):
    user_id = IntegerField()
    item = CharField()
    last_checked = DateField(null=True)   # stores last day this item was checked
    class Meta:
        database = orm_db

# the checklist defines each day from 4 am to 4 am the next day
class DailyChecklist(Model):
    user_id = IntegerField()
    item = CharField()
    last_checked = DateField(null=True)   # stores last day this item was checked
    class Meta:
        database = orm_db

def get_current_day() -> datetime.date:
    tz = pytz.timezone("America/Los_Angeles")
    now = datetime.datetime.now(tz)
    if now.hour < 4:
        now -= datetime.timedelta(days=1)
    return now.date()

def add_item(user_id: int, item: str) -> DailyChecklist:
    # Create persistent blueprint item with no check recorded
    return DailyChecklist.create(user_id=user_id, item=item, last_checked=None)

def remove_item(user_id: int, index: int) -> Tuple[bool, str]:
    # List blueprint items for the user
    query = DailyChecklist.select().where(DailyChecklist.user_id == user_id).order_by(DailyChecklist.id)
    items = list(query)
    if index < 1 or index > len(items):
        return False, "Invalid index."
    items[index - 1].delete_instance()
    return True, "Item removed."

def check_item(user_id: int, index: int) -> Tuple[bool, str]:
    current_day = get_current_day()
    query = DailyChecklist.select().where(DailyChecklist.user_id == user_id).order_by(DailyChecklist.id)
    items = list(query)
    if index < 1 or index > len(items):
        return False, "Invalid index."
    item_obj = items[index - 1]
    if item_obj.last_checked == current_day:
        return False, "Item already checked for today."
    item_obj.last_checked = current_day
    item_obj.save()
    return True, f"Item '{item_obj.item}' marked as completed for today."

def list_items(user_id: int) -> List[Tuple[str, bool]]:
    current_day = get_current_day()
    # Return tuples (item, checked) for display
    query = DailyChecklist.select().where(DailyChecklist.user_id == user_id).order_by(DailyChecklist.id)
    return [(item.item, item.last_checked == current_day) for item in query]
