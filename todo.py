import sqlite3

import discord

from errors import InvalidInputError
from log import get_ray_id, log_event

DB_NAME = "db/bot.db"


def create_db():
    """Create the database and the tasks table if they don't exist."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS todo_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        task TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        order_index INTEGER NOT NULL
    )
    """
    )
    connection.commit()
    connection.close()


def add_task(user_id: int, task: str, position: int = None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Get total task count for the user
    c.execute("SELECT COUNT(*) FROM todo_list WHERE user_id = ?", (user_id,))
    task_count = c.fetchone()[0]

    # If position is not provided or out of range, set it to the last position
    if position is None or position > task_count + 1:
        position = task_count + 1

    # Shift all tasks at or below the position down by 1
    c.execute("UPDATE todo_list SET order_index = order_index + 1 WHERE user_id = ? AND order_index >= ?", (user_id, position))

    # Insert the new task at the specified position
    c.execute("INSERT INTO todo_list (user_id, task, order_index) VALUES (?, ?, ?)", (user_id, task, position))

    conn.commit()
    conn.close()


def remove_task(user_id: int, position: int) -> str:
    tasks = list_tasks(user_id)
    task = tasks[position - 1] if tasks and position <= len(tasks) else None
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

    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # Check if task exists at the given position
    cursor.execute("SELECT id, task FROM todo_list WHERE user_id = ? AND order_index = ?", (user_id, position))
    task = cursor.fetchone()
    if not task:
        connection.close()
        return "Task not found."

    task_id = task[0]

    # Delete the task
    cursor.execute("DELETE FROM todo_list WHERE id = ?", (task_id,))

    # Shift all tasks above it up by 1
    cursor.execute("UPDATE todo_list SET order_index = order_index - 1 WHERE user_id = ? AND order_index > ?", (user_id, position))

    connection.commit()
    connection.close()

    return f"Task {position} removed: {task[1]}"


def get_task(user_id: int, position: int) -> str:
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("SELECT task FROM todo_list WHERE user_id = ? AND order_index = ?", (user_id, position))
    task = cursor.fetchone()

    connection.close()
    return task[0] if task else None


def update_task(user_id: int, position: int, new_task: str) -> None:
    tasks = list_tasks(user_id)
    task = tasks[position - 1] if tasks and position <= len(tasks) else None
    if task:
        old_task_val = getattr(task, "task", str(task))
        log_event(
            "AUDIT_LOG",
            {
                "event": "AUDIT_LOG",
                "action": "todo_edit",
                "user_id": user_id,
                "task_id": getattr(task, "id", None),
                "before": {"task": old_task_val},
                "after": {"task": new_task},
                "position": position,
                "ray_id": get_ray_id(),
            },
            level="info",
        )

    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("UPDATE todo_list SET task = ? WHERE user_id = ? AND order_index = ?", (new_task, user_id, position))
    connection.commit()
    connection.close()


def list_tasks(user_id: int):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT order_index, task
        FROM todo_list
        WHERE user_id = ?
        ORDER BY order_index ASC
    """,
        (user_id,),
    )

    tasks = cursor.fetchall()
    connection.close()

    return tasks


def move_task(user_id: int, old_position: int, new_position: int) -> str:
    tasks = list_tasks(user_id)
    task = tasks[old_position - 1] if tasks and old_position <= len(tasks) else None
    if task:
        from log import get_ray_id, log_event

        log_event(
            "AUDIT_LOG",
            {
                "event": "AUDIT_LOG",
                "action": "todo_move",
                "user_id": user_id,
                "task_id": getattr(task, "id", None),
                "before": {"position": old_position},
                "after": {"position": new_position},
                "ray_id": get_ray_id(),
            },
            level="info",
        )

    if old_position == new_position:
        return "Task is already in that position."

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Get the task's ID at old_position
    c.execute("SELECT id FROM todo_list WHERE user_id = ? AND order_index = ?", (user_id, old_position))
    task = c.fetchone()
    if not task:
        return "Task not found."

    task_id = task[0]

    # Remove gap where the task was
    c.execute("UPDATE todo_list SET order_index = order_index - 1 WHERE user_id = ? AND order_index > ?", (user_id, old_position))

    # Make space at the new position
    c.execute("UPDATE todo_list SET order_index = order_index + 1 WHERE user_id = ? AND order_index >= ?", (user_id, new_position))

    # Move the task
    c.execute("UPDATE todo_list SET order_index = ? WHERE id = ?", (new_position, task_id))

    conn.commit()
    conn.close()
    return f"Task moved to position {new_position}."


def format_task(task) -> str:
    #  task[0]:<5 ensures the Order is left-aligned and takes up 5 characters.
    return f"{task[0]:<5} | {task[1]}"


def get_tasks_response_str(tasks) -> str:
    # Format the header and all tasks using a fixed-width font
    tasks_str = "\n".join([format_task(task) for task in tasks])
    return f"**Todo List:**\n```Order | Task\n{'-' * 30}\n{tasks_str}```"


def handle_todo_command(args: list[str], user: discord.User, mentions: list[discord.User]):
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
                    add_task(user_id, task)
                    result = f"Task added: {task}"

            case "remove":
                if mentions:
                    result = "Cannot remove task using ! version for another user. please use `/todo remove` and select the user"
                elif not sub_args or not sub_args[0].isdigit():
                    result = "Please provide the ID of the task to remove."
                else:
                    position = int(sub_args[0])
                    result = remove_task(user_id, position)

            case "list":
                tasks = list_tasks(user_id)
                if tasks:
                    result = get_tasks_response_str(tasks)
                else:
                    result = "Your todo list is empty!"
            case _:
                result = f"Invalid subcommand {subcommand}. Please provide a subcommand (add, remove, list)."
    return result


class EditTaskModal(discord.ui.Modal, title="Edit Task"):
    def __init__(self, user_id: int, position: int, existing_task: str):
        super().__init__()
        self.user_id = user_id
        self.position = position

        # Prefill the text field with the existing task
        self.task_input = discord.ui.TextInput(label="Edit your task", default=existing_task, style=discord.TextStyle.long)
        self.add_item(self.task_input)

    async def on_submit(self, interaction: discord.Interaction):
        new_task = self.task_input.value
        update_task(self.user_id, self.position, new_task)
        await interaction.response.send_message(f"Task {self.position} updated successfully!")
