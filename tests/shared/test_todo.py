import pytest
from db_test_utils import wipe_table

from shared import todo
from shared.models import TodoItem

USER_ID = 1


@pytest.fixture(autouse=True)
def clear_todo_table():
    wipe_table(TodoItem)


def test_add_task_appends_by_default():
    todo.add_task(USER_ID, "Task 1")
    todo.add_task(USER_ID, "Task 2")

    tasks = todo.list_tasks(USER_ID)

    assert [task.task for task in tasks] == ["Task 1", "Task 2"]
    assert [task.order_index for task in tasks] == [1, 2]


def test_add_task_inserts_at_position_and_reorders():
    todo.add_task(USER_ID, "Task 1")
    todo.add_task(USER_ID, "Task 3")
    todo.add_task(USER_ID, "Task 2", position=2)

    tasks = todo.list_tasks(USER_ID)

    assert [task.task for task in tasks] == ["Task 1", "Task 2", "Task 3"]
    assert [task.order_index for task in tasks] == [1, 2, 3]


def test_remove_task_reorders_remaining_items():
    todo.add_task(USER_ID, "Task 1")
    todo.add_task(USER_ID, "Task 2")
    todo.add_task(USER_ID, "Task 3")

    message = todo.remove_task(USER_ID, 2)

    assert message == "Task 2 removed: Task 2"
    tasks = todo.list_tasks(USER_ID)
    assert [task.task for task in tasks] == ["Task 1", "Task 3"]
    assert [task.order_index for task in tasks] == [1, 2]


def test_remove_task_missing_position():
    assert todo.remove_task(USER_ID, 1) == "Task not found."


def test_get_and_update_task():
    todo.add_task(USER_ID, "Old Task")

    assert todo.get_task(USER_ID, 1) == "Old Task"

    todo.update_task(USER_ID, 1, "New Task")

    tasks = todo.list_tasks(USER_ID)
    assert tasks[0].task == "New Task"


def test_move_task_down():
    todo.add_task(USER_ID, "Task 1")
    todo.add_task(USER_ID, "Task 2")
    todo.add_task(USER_ID, "Task 3")

    message = todo.move_task(USER_ID, 1, 3)

    assert message == "Task moved to position 3."
    tasks = todo.list_tasks(USER_ID)
    assert [task.task for task in tasks] == ["Task 2", "Task 3", "Task 1"]
    assert [task.order_index for task in tasks] == [1, 2, 3]


def test_move_task_up():
    todo.add_task(USER_ID, "Task 1")
    todo.add_task(USER_ID, "Task 2")
    todo.add_task(USER_ID, "Task 3")

    message = todo.move_task(USER_ID, 3, 1)

    assert message == "Task moved to position 1."
    tasks = todo.list_tasks(USER_ID)
    assert [task.task for task in tasks] == ["Task 3", "Task 1", "Task 2"]
    assert [task.order_index for task in tasks] == [1, 2, 3]


def test_move_task_same_position():
    todo.add_task(USER_ID, "Task 1")

    assert todo.move_task(USER_ID, 1, 1) == "Task is already in that position."


def test_move_task_missing_position():
    todo.add_task(USER_ID, "Task 1")

    assert todo.move_task(USER_ID, 1, 2) == "Task not found."


def test_list_tasks_isolated_by_user():
    todo.add_task(1, "User 1 Task 1")
    todo.add_task(1, "User 1 Task 2")
    todo.add_task(2, "User 2 Task 1")

    tasks_user_1 = todo.list_tasks(1)
    tasks_user_2 = todo.list_tasks(2)

    assert [task.task for task in tasks_user_1] == ["User 1 Task 1", "User 1 Task 2"]
    assert [task.task for task in tasks_user_2] == ["User 2 Task 1"]


def test_format_task_supports_model_instances():
    task = TodoItem(user_id=USER_ID, task="Formatted Task", order_index=4)
    assert todo.format_task(task) == "4     | Formatted Task"


def test_get_tasks_response_str_uses_order_and_task_text():
    todo.add_task(USER_ID, "Task 1")
    todo.add_task(USER_ID, "Task 2")

    response = todo.get_tasks_response_str(todo.list_tasks(USER_ID))

    assert "**Todo List:**" in response
    assert "1     | Task 1" in response
    assert "2     | Task 2" in response
