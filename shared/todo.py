from __future__ import annotations

import datetime
from collections.abc import Sequence

import discord

from .errors import InvalidInputError
from .log import get_ray_id, log_event, ray_id_var
from .models import TodoItem, orm_db


def create_db():
    """Retained for backward compatibility; todo now lives in the ORM database."""
    orm_db.connect(reuse_if_open=True)


def _active_scope(user_id: int, guild_id: int | None):
    guild_filter = TodoItem.guild_id.is_null() if guild_id is None else (TodoItem.guild_id == guild_id)
    return (TodoItem.user_id == user_id) & guild_filter & TodoItem.completed_at.is_null()


def _get_user_tasks(user_id: int, guild_id: int | None) -> list[TodoItem]:
    return list(TodoItem.select().where(_active_scope(user_id, guild_id)).order_by(TodoItem.order_index, TodoItem.id))


def _get_task_by_position(user_id: int, guild_id: int | None, position: int) -> TodoItem | None:
    if position < 1:
        return None
    return TodoItem.select().where(_active_scope(user_id, guild_id), TodoItem.order_index == position).order_by(TodoItem.id).first()


def add_task(user_id: int, task: str, position: int = None, guild_id: int | None = None):
    task_count = TodoItem.select().where(_active_scope(user_id, guild_id)).count()

    if position is None or position < 1 or position > task_count + 1:
        position = task_count + 1

    with orm_db.atomic():
        (
            TodoItem.update({TodoItem.order_index: TodoItem.order_index + 1})
            .where(_active_scope(user_id, guild_id), TodoItem.order_index >= position)
            .execute()
        )
        return TodoItem.create(user_id=user_id, guild_id=guild_id, task=task, order_index=position)


def remove_task(user_id: int, position: int, guild_id: int | None = None) -> str:
    task = _get_task_by_position(user_id, guild_id, position)
    if task:
        log_event(
            "AUDIT_LOG",
            {
                "event": "AUDIT_LOG",
                "action": "todo_remove",
                "user_id": user_id,
                "task_id": getattr(task, "id", None),
                "before": {"task": getattr(task, "task", str(task)), "position": position},
                "ray_id": get_ray_id(),
            },
            level="info",
        )
    if not task:
        return "Task not found."

    removed_task = task.task
    with orm_db.atomic():
        task.completed_at = datetime.datetime.now()
        task.order_index = -1
        task.save()
        (
            TodoItem.update({TodoItem.order_index: TodoItem.order_index - 1})
            .where(_active_scope(user_id, guild_id), TodoItem.order_index > position)
            .execute()
        )

    return f"Task {position} removed: {removed_task}"


def get_task(user_id: int, position: int, guild_id: int | None = None) -> str:
    task = _get_task_by_position(user_id, guild_id, position)
    return task.task if task else None


def update_task(user_id: int, position: int, new_task: str, guild_id: int | None = None) -> None:
    task = _get_task_by_position(user_id, guild_id, position)
    if task:
        log_event(
            "AUDIT_LOG",
            {
                "event": "AUDIT_LOG",
                "ray_id": get_ray_id(),
                "action": "todo_edit",
                "user_id": user_id,
                "task_id": task.id,
                "before": {"task": task.task},
                "after": {"task": new_task},
                "position": position,
            },
            level="info",
        )
        task.task = new_task
        task.save()


def list_tasks(user_id: int, guild_id: int | None = None):
    return _get_user_tasks(user_id, guild_id)


def move_task(user_id: int, old_position: int, new_position: int, guild_id: int | None = None) -> str:
    tasks = list_tasks(user_id, guild_id)
    task = tasks[old_position - 1] if tasks and old_position <= len(tasks) else None
    if task:
        log_event(
            "AUDIT_LOG",
            {
                "event": "AUDIT_LOG",
                "action": "todo_move",
                "user_id": user_id,
                "task_id": task.id,
                "before": {"position": old_position},
                "after": {"position": new_position},
                "ray_id": get_ray_id(),
            },
            level="info",
        )

    if old_position == new_position:
        return "Task is already in that position."

    task_count = len(tasks)
    if old_position < 1 or old_position > task_count or new_position < 1 or new_position > task_count:
        return "Task not found."

    item_to_move = task
    with orm_db.atomic():
        if old_position < new_position:
            (
                TodoItem.update({TodoItem.order_index: TodoItem.order_index - 1})
                .where(
                    _active_scope(user_id, guild_id),
                    TodoItem.order_index > old_position,
                    TodoItem.order_index <= new_position,
                )
                .execute()
            )
        else:
            (
                TodoItem.update({TodoItem.order_index: TodoItem.order_index + 1})
                .where(
                    _active_scope(user_id, guild_id),
                    TodoItem.order_index >= new_position,
                    TodoItem.order_index < old_position,
                )
                .execute()
            )

        item_to_move.order_index = new_position
        item_to_move.save()

    return f"Task moved to position {new_position}."


def format_task(task) -> str:
    #  task[0]:<5 ensures the Order is left-aligned and takes up 5 characters.
    if isinstance(task, Sequence) and not isinstance(task, str):
        return f"{task[0]:<5} | {task[1]}"
    return f"{task.order_index:<5} | {task.task}"


def get_tasks_response_str(tasks) -> str:
    # Format the header and all tasks using a fixed-width font
    tasks_str = "\n".join([format_task(task) for task in tasks])
    return f"**Todo List:**\n```Order | Task\n{'-' * 30}\n{tasks_str}```"


def handle_todo_command(args: list[str], user: discord.User, mentions: list[discord.User], guild_id: int | None = None):
    result = None
    if not args:
        result = "Please provide a subcommand (add, remove, list)."
    else:
        subcommand = args[0].lower()
        sub_args = args[1:]

        if len(mentions) > 1:
            raise InvalidInputError("Can only work on one todo list at a time. Do not mention Multiple users")

        if len(mentions) == 1:
            user = mentions[0]

        user_id = user.id

        match subcommand:
            case "add":
                if not sub_args:
                    result = "Please provide a task to add."
                else:
                    task = " ".join(sub_args)
                    add_task(user_id, task, guild_id=guild_id)
                    result = f"Task added: {task}"

            case "remove":
                if mentions:
                    result = "Cannot remove task using ! version for another user. please use `/todo remove` and select the user"
                elif not sub_args or not sub_args[0].isdigit():
                    result = "Please provide the ID of the task to remove."
                else:
                    position = int(sub_args[0])
                    result = remove_task(user_id, position, guild_id)

            case "list":
                tasks = list_tasks(user_id, guild_id)
                if tasks:
                    result = get_tasks_response_str(tasks)
                else:
                    result = "Your todo list is empty!"
            case _:
                result = f"Invalid subcommand {subcommand}. Please provide a subcommand (add, remove, list)."
    return result


class EditTaskModal(discord.ui.Modal, title="Edit Task"):
    def __init__(self, user_id: int, guild_id: int | None, position: int, existing_task: str):
        super().__init__()
        self.user_id = user_id
        self.guild_id = guild_id
        self.position = position
        self.ray_id = get_ray_id()

        # Prefill the text field with the existing task
        self.task_input = discord.ui.TextInput(label="Edit your task", default=existing_task, style=discord.TextStyle.long)
        self.add_item(self.task_input)

    async def on_submit(self, interaction: discord.Interaction):
        token = ray_id_var.set(self.ray_id)
        try:
            new_task = self.task_input.value
            update_task(self.user_id, self.position, new_task, self.guild_id)
            await interaction.response.send_message(f"Task {self.position} updated successfully!")
        finally:
            ray_id_var.reset(token)
