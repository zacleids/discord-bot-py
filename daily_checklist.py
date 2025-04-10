import datetime
import pytz
from peewee import Model, IntegerField, CharField, DateField, SQL
from db.db import orm_db
from typing import Tuple, List
import discord

class DailyChecklist(Model):
    user_id = IntegerField()
    item = CharField()
    last_checked = DateField(null=True)   # stores last day this item was checked
    sort_order = IntegerField(constraints=[SQL('DEFAULT 0')])
    class Meta:
        database = orm_db

def get_current_day() -> datetime.date:
    tz = pytz.timezone("America/Los_Angeles")
    now = datetime.datetime.now(tz)
    if now.hour < 4:
        now -= datetime.timedelta(days=1)
    return now.date()

def add_item(user_id: int, item: str) -> DailyChecklist:
    # Get max sort_order for this user
    max_order = (DailyChecklist
                 .select(DailyChecklist.sort_order)
                 .where(DailyChecklist.user_id == user_id)
                 .order_by(DailyChecklist.sort_order.desc())
                 .first())
    next_order = (max_order.sort_order + 1) if max_order else 1  # Start at 1
    return DailyChecklist.create(user_id=user_id, item=item, last_checked=None, sort_order=next_order)

def remove_item(user_id: int, position: int) -> Tuple[bool, str]:
    # Find item by sort_order directly
    item = (DailyChecklist
            .select()
            .where(DailyChecklist.user_id == user_id, DailyChecklist.sort_order == position)
            .first())
    if not item:
        return False, "Invalid position."
    
    # Delete the item and reorder remaining items
    with orm_db.atomic():
        # Delete the target item
        item.delete_instance()
        # Shift down all items after this one
        query = (DailyChecklist
                .update({DailyChecklist.sort_order: DailyChecklist.sort_order - 1})
                .where(DailyChecklist.user_id == user_id, 
                       DailyChecklist.sort_order > position))
        query.execute()
    return True, "Item removed."

def check_item(user_id: int, position: int) -> Tuple[bool, str]:
    current_day = get_current_day()
    # Find item by sort_order directly
    item = (DailyChecklist
            .select()
            .where(DailyChecklist.user_id == user_id, DailyChecklist.sort_order == position)
            .first())
    if not item:
        return False, "Invalid position."
    if item.last_checked == current_day:
        return False, "Item already checked for today."
    item.last_checked = current_day
    item.save()
    return True, f"Item '{item.item}' marked as completed for today."

def uncheck_item(user_id: int, position: int) -> Tuple[bool, str]:
    item = (DailyChecklist
            .select()
            .where(DailyChecklist.user_id == user_id, DailyChecklist.sort_order == position)
            .first())
    if not item:
        return False, "Invalid position."
    item.last_checked = None
    item.save()
    return True, f"Item '{item.item}' unchecked."

def list_items(user_id: int) -> List[DailyChecklist]:
    return list(DailyChecklist
             .select()
             .where(DailyChecklist.user_id == user_id)
             .order_by(DailyChecklist.sort_order))

def edit_item(user_id: int, position: int, new_text: str) -> Tuple[bool, str]:
    # Find item by sort_order directly
    item = (DailyChecklist
            .select()
            .where(DailyChecklist.user_id == user_id, DailyChecklist.sort_order == position)
            .first())
    if not item:
        return False, "Invalid position."
    item.item = new_text
    item.save()
    return True, "Item updated."

def move_item(user_id: int, old_pos: int, new_pos: int) -> Tuple[bool, str]:
    # Verify positions are valid
    count = (DailyChecklist
             .select()
             .where(DailyChecklist.user_id == user_id)
             .count())
    if old_pos < 1 or old_pos > count or new_pos < 1 or new_pos > count:
        return False, "Invalid position."
    
    # Get item to move
    item_to_move = (DailyChecklist
                    .select()
                    .where(DailyChecklist.user_id == user_id, 
                           DailyChecklist.sort_order == old_pos)
                    .first())
    if not item_to_move:
        return False, "Item not found."
    
    with orm_db.atomic():
        if old_pos < new_pos:
            # Moving down: shift items up
            (DailyChecklist
             .update({DailyChecklist.sort_order: DailyChecklist.sort_order - 1})
             .where(DailyChecklist.user_id == user_id,
                    DailyChecklist.sort_order > old_pos,
                    DailyChecklist.sort_order <= new_pos)
             .execute())
        else:
            # Moving up: shift items down
            (DailyChecklist
             .update({DailyChecklist.sort_order: DailyChecklist.sort_order + 1})
             .where(DailyChecklist.user_id == user_id,
                    DailyChecklist.sort_order >= new_pos,
                    DailyChecklist.sort_order < old_pos)
             .execute())
        
        item_to_move.sort_order = new_pos
        item_to_move.save()
    
    return True, f"Moved item from position {old_pos} to {new_pos}."

class EditDailyItemModal(discord.ui.Modal, title="Edit Daily Item"):
    def __init__(self, user_id: int, index: int, existing_text: str):
        super().__init__()
        self.user_id = user_id
        self.index = index
        
        self.text_input = discord.ui.TextInput(
            label="Edit item text",
            default=existing_text,
            style=discord.TextStyle.short,
            max_length=100
        )
        self.add_item(self.text_input)

    async def on_submit(self, interaction: discord.Interaction):
        success, msg = edit_item(self.user_id, self.index, self.text_input.value)
        await interaction.response.send_message(msg, ephemeral=not success)

def handle_daily_checklist_command(args: list[str], user) -> str:
    if not args:
        return "Please provide a subcommand (add, remove, list, check, move, uncheck)"

    subcommand = args[0].lower()
    sub_args = args[1:]

    match subcommand:
        case "add":
            if not sub_args:
                return "Please provide an item to add."
            item = " ".join(sub_args)
            add_item(user.id, item)
            return f"Item added: {item}"

        case "list":
            items = list_items(user.id)
            if not items:
                return "Your daily checklist is empty."
            
            response = "**Your Daily Checklist:**\n"
            current_day = get_current_day()
            for idx, item in enumerate(items, start=1):
                status = "✅" if item.last_checked == current_day else "❌"
                response += f"{item.sort_order}. {item.item} [{status}])\n"
            return response

        case "remove":
            if not sub_args:
                return "Please provide the position of the item to remove."
            try:
                position = int(sub_args[0])
                success, msg = remove_item(user.id, position)
                return msg
            except ValueError:
                return "Please provide a valid number for the position."

        case "check":
            if not sub_args:
                return "Please provide the position of the item to check off."
            try:
                position = int(sub_args[0])
                success, msg = check_item(user.id, position)
                return msg
            except ValueError:
                return "Please provide a valid number for the position."

        case "uncheck":
            if not sub_args:
                return "Please provide the position of the item to uncheck."
            try:
                position = int(sub_args[0])
                success, msg = uncheck_item(user.id, position)
                return msg
            except ValueError:
                return "Please provide a valid number for the position."

        case "move":
            if len(sub_args) < 2:
                return "Please provide both old and new positions."
            try:
                old_pos = int(sub_args[0])
                new_pos = int(sub_args[1])
                success, msg = move_item(user.id, old_pos, new_pos)
                return msg
            except ValueError:
                return "Please provide valid numbers for positions."

        case _:
            return f"Invalid subcommand '{subcommand}'. Available subcommands: add, remove, list, check, uncheck, move"
