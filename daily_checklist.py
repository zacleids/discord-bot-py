import datetime
import pytz
from models import orm_db, DailyChecklist, DailyChecklistCheck
from log import log_event, get_ray_id
from typing import Tuple, List
import discord


def get_current_day() -> datetime.date:
    tz = pytz.timezone("America/Los_Angeles")
    now = datetime.datetime.now(tz)
    if now.hour < 4:
        now -= datetime.timedelta(days=1)
    return now.date()


def add_item(user_id: int, item: str) -> DailyChecklist:
    # Get max sort_order for this user
    max_order = (
        DailyChecklist.select(DailyChecklist.sort_order)
        .where(DailyChecklist.user_id == user_id, DailyChecklist.deleted_at.is_null())
        .order_by(DailyChecklist.sort_order.desc())
        .first()
    )
    next_order = (max_order.sort_order + 1) if max_order else 1  # Start at 1
    return DailyChecklist.create(user_id=user_id, item=item, sort_order=next_order)


def remove_item(user_id: int, position: int) -> Tuple[bool, str]:
    # Find item by sort_order directly
    item = (
        DailyChecklist.select()
        .where(DailyChecklist.user_id == user_id, DailyChecklist.sort_order == position, DailyChecklist.deleted_at.is_null())
        .first()
    )
    if not item:
        return False, "Invalid position."
    log_event(
        "AUDIT_LOG",
        {
            "event": "AUDIT_LOG",
            "action": "daily_checklist_remove",
            "user_id": user_id,
            "item_id": item.id,
            "before": {"item": item.item, "position": position},
            "ray_id": get_ray_id(),
        },
        level="info",
    )
    # Soft delete the item and set its sort_order to 0
    with orm_db.atomic():
        # First shift down all items after this one
        query = DailyChecklist.update({DailyChecklist.sort_order: DailyChecklist.sort_order - 1}).where(
            DailyChecklist.user_id == user_id, DailyChecklist.sort_order > position, DailyChecklist.deleted_at.is_null()
        )
        query.execute()

        # Then mark this item as deleted and reset its sort order
        item.deleted_at = datetime.datetime.now()
        item.sort_order = 0  # Reset sort_order when deleted
        item.save()

    return True, "Item removed."


def check_item(user_id: int, position: int) -> Tuple[bool, str]:
    current_day = get_current_day()
    item = (
        DailyChecklist.select()
        .where(DailyChecklist.user_id == user_id, DailyChecklist.sort_order == position, DailyChecklist.deleted_at.is_null())
        .first()
    )
    if not item:
        return False, "Invalid position."

    _, is_checked = is_item_checked(item, current_day)
    if is_checked:
        return False, "Item already checked for today."

    DailyChecklistCheck.create(checklist_item=item, checked_at=current_day)
    return True, f"Item '{item.item}' marked as completed for today."


def uncheck_item(user_id: int, position: int) -> Tuple[bool, str]:
    current_day = get_current_day()
    item = (
        DailyChecklist.select()
        .where(DailyChecklist.user_id == user_id, DailyChecklist.sort_order == position, DailyChecklist.deleted_at.is_null())
        .first()
    )
    if not item:
        return False, "Invalid position."

    check = DailyChecklistCheck.get_or_none(checklist_item=item, checked_at=current_day)
    if not check:
        return False, "Item is not checked."

    check.delete_instance()
    return True, f"Item '{item.item}' unchecked."


def is_item_checked(item: DailyChecklist, day: datetime.date) -> Tuple[DailyChecklistCheck, bool]:
    check = DailyChecklistCheck.get_or_none(checklist_item=item, checked_at=day)
    return check, check is not None


def list_items(user_id: int) -> List[DailyChecklist]:
    """List current active items. For display, use get_checklist_for_date instead."""
    return list(
        DailyChecklist.select()
        .where(DailyChecklist.user_id == user_id, DailyChecklist.deleted_at.is_null())
        .order_by(DailyChecklist.sort_order)
    )


def get_checklist_for_date(user_id: int, date: datetime.date) -> List[Tuple[DailyChecklist, bool]]:
    """Get checklist items and their check status for a specific date"""
    # Convert date to datetime in PT for proper day boundaries (4am cutoff)
    tz = pytz.timezone("America/Los_Angeles")
    date_start = datetime.datetime.combine(date, datetime.time(4, 0))  # 4am PT on the target date
    date_start = tz.localize(date_start)
    date_end = date_start + datetime.timedelta(days=1)  # 4am PT the next day

    # Convert to UTC for database comparison since created_at is stored in UTC
    date_end_utc = date_end.astimezone(pytz.UTC)

    items = list(
        DailyChecklist.select()
        .where(
            DailyChecklist.user_id == user_id,
            DailyChecklist.created_at <= date_end_utc,  # Item existed on that date
            (DailyChecklist.deleted_at.is_null())  # Either not deleted
            | (DailyChecklist.deleted_at > date_end_utc),  # Or deleted after that date
        )
        .order_by(DailyChecklist.sort_order)
    )

    return [(item, is_item_checked(item, date)[1]) for item in items]


def edit_item(user_id: int, position: int, new_text: str) -> Tuple[bool, str]:
    # Find item by sort_order directly
    item = (
        DailyChecklist.select()
        .where(DailyChecklist.user_id == user_id, DailyChecklist.sort_order == position, DailyChecklist.deleted_at.is_null())
        .first()
    )
    if not item:
        return False, "Invalid position."
    old_text = item.item
    log_event(
        "AUDIT_LOG",
        {
            "event": "AUDIT_LOG",
            "action": "daily_checklist_edit",
            "user_id": user_id,
            "item_id": item.id,
            "before": {"item": old_text},
            "after": {"item": new_text},
            "position": position,
            "ray_id": get_ray_id(),
        },
        level="info",
    )
    item.item = new_text
    item.save()
    return True, "Item updated."


def move_item(user_id: int, old_pos: int, new_pos: int) -> Tuple[bool, str]:
    # Verify positions are valid
    count = DailyChecklist.select().where(DailyChecklist.user_id == user_id, DailyChecklist.deleted_at.is_null()).count()
    if old_pos < 1 or old_pos > count or new_pos < 1 or new_pos > count:
        return False, "Invalid position."

    # Get item to move
    item_to_move = (
        DailyChecklist.select()
        .where(DailyChecklist.user_id == user_id, DailyChecklist.sort_order == old_pos, DailyChecklist.deleted_at.is_null())
        .first()
    )
    if not item_to_move:
        return False, "Item not found."

    log_event(
        "AUDIT_LOG",
        {
            "event": "AUDIT_LOG",
            "action": "daily_checklist_move",
            "user_id": user_id,
            "item_id": item_to_move.id,
            "before": {"position": old_pos},
            "after": {"position": new_pos},
            "ray_id": get_ray_id(),
        },
        level="info",
    )
    with orm_db.atomic():
        if old_pos < new_pos:
            # Moving down: shift items up
            (
                DailyChecklist.update({DailyChecklist.sort_order: DailyChecklist.sort_order - 1})
                .where(
                    DailyChecklist.user_id == user_id,
                    DailyChecklist.sort_order > old_pos,
                    DailyChecklist.sort_order <= new_pos,
                    DailyChecklist.deleted_at.is_null(),
                )
                .execute()
            )
        else:
            # Moving up: shift items down
            (
                DailyChecklist.update({DailyChecklist.sort_order: DailyChecklist.sort_order + 1})
                .where(
                    DailyChecklist.user_id == user_id,
                    DailyChecklist.sort_order >= new_pos,
                    DailyChecklist.sort_order < old_pos,
                    DailyChecklist.deleted_at.is_null(),
                )
                .execute()
            )

        item_to_move.sort_order = new_pos
        item_to_move.save()

    return True, f"Moved item from position {old_pos} to {new_pos}."


class EditDailyItemModal(discord.ui.Modal, title="Edit Daily Item"):
    def __init__(self, user_id: int, index: int, existing_text: str):
        super().__init__()
        self.user_id = user_id
        self.index = index

        self.text_input = discord.ui.TextInput(label="Edit item text", default=existing_text, style=discord.TextStyle.short, max_length=100)
        self.add_item(self.text_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Try to get the old value
        try:
            items = list_items(self.user_id)
            old_item = items[self.index - 1] if items and self.index <= len(items) else None
            old_text = old_item.item if old_item else None
        except Exception:
            old_text = None
        new_text = self.text_input.value
        log_event(
            "AUDIT_LOG",
            {
                "event": "AUDIT_LOG",
                "action": "daily_checklist_edit",
                "user_id": interaction.user.id,
                "item_id": getattr(old_item, "id", None) if old_item else None,
                "before": {"item": old_text},
                "after": {"item": new_text},
                "position": self.index,
                "ray_id": get_ray_id(),
            },
            level="info",
        )
        success, msg = edit_item(self.user_id, self.index, new_text)
        await interaction.response.send_message(msg, ephemeral=not success)


def format_checklist_response(items: List[Tuple[DailyChecklist, bool]], date: datetime.date) -> str:
    if not items:
        return "Your daily checklist" + (f" for {date.strftime('%Y-%m-%d')}" if date != get_current_day() else "") + " is empty."

    header = "**Your Daily Checklist" + (f" for {date.strftime('%Y-%m-%d')}" if date != get_current_day() else "") + ":**\n"

    all_checked = all(checked for _, checked in items)
    response_lines = [f"{item.sort_order}. {item.item} [{'✅' if checked else '❌'}]" for item, checked in items]

    response = header + "\n".join(response_lines)
    if all_checked and items:  # Only congratulate if there are items and all are checked
        response += "\n\n🎉 Congratulations! All items completed!"

    return response


def handle_daily_checklist_command(args: list[str], user) -> str:
    if not args:
        return "Please provide a subcommand (add, remove, list, check, uncheck, move, history)"

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
            current_day = get_current_day()
            items = get_checklist_for_date(user.id, current_day)
            return format_checklist_response(items, current_day)

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

        case "history":
            try:
                if sub_args:
                    target_date = datetime.datetime.strptime(sub_args[0], "%Y-%m-%d").date()
                else:
                    target_date = get_current_day()
                items = get_checklist_for_date(user.id, target_date)
                return format_checklist_response(items, target_date)
            except ValueError:
                return "Invalid date format. Please use YYYY-MM-DD"

        case _:
            return f"Invalid subcommand '{subcommand}'. Available subcommands: add, remove, list, check, uncheck, move, history"
