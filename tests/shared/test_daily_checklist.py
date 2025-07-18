import datetime

import pytest
from db_test_utils import wipe_table

from shared import daily_checklist
from shared.models import DailyChecklist, DailyChecklistCheck

FAKE_NOW = datetime.datetime(2025, 5, 25, tzinfo=datetime.timezone.utc)
USER_ID = 1


@pytest.fixture(autouse=True)
def clear_tables_before_each_test():
    # Wipe relevant tables before each test
    wipe_table(DailyChecklistCheck)
    wipe_table(DailyChecklist)


def test_add_item():
    item_text = "Test Task"
    item = daily_checklist.add_item(USER_ID, item_text)
    assert item.item == item_text
    assert item.user_id == USER_ID
    assert item.sort_order == 1
    items = daily_checklist.list_items(USER_ID)
    assert len(items) == 1
    assert items[0].item == item_text


def test_remove_item():
    daily_checklist.add_item(USER_ID, "Task 1")
    daily_checklist.add_item(USER_ID, "Task 2")
    success, msg = daily_checklist.remove_item(USER_ID, 1)
    assert success
    items = daily_checklist.list_items(USER_ID)
    assert len(items) == 1
    assert items[0].sort_order == 1  # Remaining item should be re-ordered


def test_check_and_uncheck_item():
    daily_checklist.add_item(USER_ID, "Task 1")
    success, msg = daily_checklist.check_item(USER_ID, 1)
    assert success
    current_day = daily_checklist.get_current_day()
    items = daily_checklist.get_checklist_for_date(USER_ID, current_day)
    assert items[0][1] is True  # Checked
    success, msg = daily_checklist.uncheck_item(USER_ID, 1)
    assert success
    items = daily_checklist.get_checklist_for_date(USER_ID, current_day)
    assert items[0][1] is False  # Unchecked


def test_edit_item():
    daily_checklist.add_item(USER_ID, "Old Task")
    success, msg = daily_checklist.edit_item(USER_ID, 1, "New Task")
    assert success
    items = daily_checklist.list_items(USER_ID)
    assert items[0].item == "New Task"


def test_move_item():
    daily_checklist.add_item(USER_ID, "Task 1")
    daily_checklist.add_item(USER_ID, "Task 2")
    daily_checklist.add_item(USER_ID, "Task 3")
    success, msg = daily_checklist.move_item(USER_ID, 1, 3)
    assert success
    items = daily_checklist.list_items(USER_ID)
    assert items[0].item == "Task 2"
    assert items[1].item == "Task 3"
    assert items[2].item == "Task 1"


def test_multiple_users_isolation():
    # User 1 adds two tasks
    user1 = 10
    daily_checklist.add_item(user1, "User1 Task 1")
    daily_checklist.add_item(user1, "User1 Task 2")

    # User 2 adds two tasks
    user2 = 20
    daily_checklist.add_item(user2, "User2 Task 1")
    daily_checklist.add_item(user2, "User2 Task 2")

    # Move User 1's first task to position 2
    success, msg = daily_checklist.move_item(user1, 1, 2)
    assert success

    # Check User 1's tasks are reordered
    items_user1 = daily_checklist.list_items(user1)
    assert items_user1[0].item == "User1 Task 2"
    assert items_user1[1].item == "User1 Task 1"
    assert items_user1[0].sort_order == 1
    assert items_user1[1].sort_order == 2

    # Check User 2's tasks are unaffected
    items_user2 = daily_checklist.list_items(user2)
    assert items_user2[0].item == "User2 Task 1"
    assert items_user2[1].item == "User2 Task 2"
    assert items_user2[0].sort_order == 1
    assert items_user2[1].sort_order == 2


def test_get_checklist_for_previous_date():
    # Setup: create a checklist item for a previous date
    previous_date = datetime.date.today() - datetime.timedelta(days=2)
    # Insert item directly into the DB with created_at set to previous_date
    DailyChecklist.create(
        user_id=USER_ID, item="Old Task", sort_order=1, created_at=datetime.datetime.combine(previous_date, datetime.time(12, 0))
    )
    # Should be visible for that date
    items_prev = daily_checklist.get_checklist_for_date(USER_ID, previous_date)
    assert len(items_prev) == 1
    assert items_prev[0][0].item == "Old Task"
    # Should also be visible for today (not deleted)
    today = datetime.date.today()
    items_today = daily_checklist.get_checklist_for_date(USER_ID, today)
    assert len(items_today) == 1
    assert items_today[0][0].item == "Old Task"


def test_remove_nonexistent_item():
    # Try to remove an item that doesn't exist
    success, msg = daily_checklist.remove_item(USER_ID, 1)
    assert not success
    assert "invalid position" in msg.lower()


def test_check_nonexistent_item():
    # Try to check an item that doesn't exist
    success, msg = daily_checklist.check_item(USER_ID, 1)
    assert not success
    assert "invalid position" in msg.lower()


def test_uncheck_nonexistent_item():
    # Try to uncheck an item that doesn't exist
    success, msg = daily_checklist.uncheck_item(USER_ID, 1)
    assert not success
    assert "invalid position" in msg.lower()


def test_edit_nonexistent_item():
    # Try to edit an item that doesn't exist
    success, msg = daily_checklist.edit_item(USER_ID, 1, "Should Fail")
    assert not success
    assert "invalid position" in msg.lower()


def test_move_nonexistent_item():
    # Try to move an item that doesn't exist
    success, msg = daily_checklist.move_item(USER_ID, 1, 2)
    assert not success
    assert "invalid position" in msg.lower()


def test_move_to_invalid_position():
    daily_checklist.add_item(USER_ID, "Only Task")
    # Try to move to an invalid position (e.g., 0 or beyond list length)
    success, msg = daily_checklist.move_item(USER_ID, 1, 0)
    assert not success
    assert "invalid position" in msg.lower()
    success, msg = daily_checklist.move_item(USER_ID, 1, 5)
    assert not success
    assert "invalid position" in msg.lower()


def test_check_already_checked_item():
    daily_checklist.add_item(USER_ID, "Test Task")
    # First check should succeed
    success, msg = daily_checklist.check_item(USER_ID, 1)
    assert success
    # Second check should fail (already checked)
    success, msg = daily_checklist.check_item(USER_ID, 1)
    assert not success
    assert "already checked" in msg.lower()


def test_uncheck_unchecked_item():
    daily_checklist.add_item(USER_ID, "Test Task")
    # Uncheck should fail (not checked yet)
    success, msg = daily_checklist.uncheck_item(USER_ID, 1)
    assert not success
    assert "not checked" in msg.lower()


def test_format_checklist_response_empty():
    date = daily_checklist.get_current_day()
    items = daily_checklist.get_checklist_for_date(USER_ID, date)
    response = daily_checklist.format_checklist_response(items, date)
    assert "is empty" in response.lower()


def test_format_checklist_response_one_item():
    date = daily_checklist.get_current_day()
    daily_checklist.add_item(USER_ID, "Solo Task")
    items = daily_checklist.get_checklist_for_date(USER_ID, date)
    response = daily_checklist.format_checklist_response(items, date)
    assert "1. Solo Task" in response
    assert "❌" in response


def test_format_checklist_response_ten_items():
    date = daily_checklist.get_current_day()
    for i in range(10):
        daily_checklist.add_item(USER_ID, f"Task {i+1}")
    items = daily_checklist.get_checklist_for_date(USER_ID, date)
    response = daily_checklist.format_checklist_response(items, date)
    for i in range(10):
        assert f"{i+1}. Task {i+1}" in response
    assert response.count("❌") == 10


def test_format_checklist_response_four_same_name_some_checked():
    date = daily_checklist.get_current_day()
    for _ in range(4):
        daily_checklist.add_item(USER_ID, "Repeat Task")
    # Check 1st and 3rd
    daily_checklist.check_item(USER_ID, 1)
    daily_checklist.check_item(USER_ID, 3)
    items = daily_checklist.get_checklist_for_date(USER_ID, date)
    response = daily_checklist.format_checklist_response(items, date)
    assert response.count("Repeat Task") == 4
    # 1st and 3rd checked, 2nd and 4th unchecked
    lines = response.splitlines()
    assert "1. Repeat Task [✅]" in lines[1]
    assert "2. Repeat Task [❌]" in lines[2]
    assert "3. Repeat Task [✅]" in lines[3]
    assert "4. Repeat Task [❌]" in lines[4]


def test_format_checklist_response_all_checked():
    date = daily_checklist.get_current_day()
    for i in range(4):
        daily_checklist.add_item(USER_ID, f"Task {i+1}")
        daily_checklist.check_item(USER_ID, i + 1)
    items = daily_checklist.get_checklist_for_date(USER_ID, date)
    response = daily_checklist.format_checklist_response(items, date)
    assert response.count("✅") == 4
    assert "congratulations" in response.lower()
    assert "all items" in response.lower()
