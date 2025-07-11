from datetime import datetime

from flask import Blueprint, request

from shared import daily_checklist
from shared.log import log_and_send_json_response, log_request
from web.backend.middleware import require_discord_id

daily_checklist_bp = Blueprint("daily_checklist", __name__, url_prefix="/daily")


@daily_checklist_bp.route("/add", methods=["POST"])
@log_request
@require_discord_id
def add_item():
    """
    Add an item to your daily checklist
    ---
    tags: [Daily Checklist]
    parameters:
      - in: header
        name: X-Discord-Id
        required: true
        type: string
        description: Discord user ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            item:
              type: string
              description: The item to add
              example: Complete daily report
          required:
            - item
    responses:
      200:
        description: Item added
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
    """
    discord_id = int(request.headers["X-Discord-Id"])
    data = request.get_json()
    item = data.get("item")
    if not item:
        return log_and_send_json_response({"status": "error", "message": "Missing item"}, status_code=400)
    daily_checklist.add_item(discord_id, item)
    return log_and_send_json_response({"status": "success", "message": f"Item added: {item}"})


@daily_checklist_bp.route("/remove", methods=["POST"])
@log_request
@require_discord_id
def remove_item():
    """
    Remove an item by its position
    ---
    tags: [Daily Checklist]
    parameters:
      - in: header
        name: X-Discord-Id
        required: true
        type: string
        description: Discord user ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            position:
              type: integer
              description: The position of the item to remove (1-based)
              example: 1
          required:
            - position
    responses:
      200:
        description: Item removed
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
    """
    discord_id = int(request.headers["X-Discord-Id"])
    data = request.get_json()
    position = data.get("position")
    if not position:
        return log_and_send_json_response({"status": "error", "message": "Missing position"}, status_code=400)
    success, msg = daily_checklist.remove_item(discord_id, position)
    return log_and_send_json_response({"status": "success" if success else "error", "message": msg})


@daily_checklist_bp.route("/list", methods=["GET"])
@log_request
@require_discord_id
def list_items():
    """
    List your daily checklist items for today
    ---
    tags: [Daily Checklist]
    parameters:
      - in: header
        name: X-Discord-Id
        required: true
        schema:
          type: string
        description: Discord user ID
    responses:
      200:
        description: Checklist items
        schema:
          type: object
          properties:
            status:
              type: string
            items:
              type: array
              items:
                type: object
            message:
              type: string
    """
    discord_id = int(request.headers["X-Discord-Id"])
    current_day = daily_checklist.get_current_day()
    items = daily_checklist.get_checklist_for_date(discord_id, current_day)
    response = daily_checklist.format_checklist_response(items, current_day)
    serialized_items = [{"item": item.item, "position": item.sort_order, "checked": checked} for item, checked in items]
    return log_and_send_json_response({"status": "success", "items": serialized_items, "message": response})


@daily_checklist_bp.route("/check", methods=["POST"])
@log_request
@require_discord_id
def check_item():
    """
    Mark an item as completed by its position
    ---
    tags: [Daily Checklist]
    parameters:
      - in: header
        name: X-Discord-Id
        required: true
        type: string
        description: Discord user ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            position:
              type: integer
              description: The position of the item to check (1-based)
              example: 1
          required:
            - position
    responses:
      200:
        description: Item checked
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
    """
    discord_id = int(request.headers["X-Discord-Id"])
    data = request.get_json()
    position = data.get("position")
    if not position:
        return log_and_send_json_response({"status": "error", "message": "Missing position"}, status_code=400)
    success, msg = daily_checklist.check_item(discord_id, position)
    return log_and_send_json_response({"status": "success" if success else "error", "message": msg})


@daily_checklist_bp.route("/uncheck", methods=["POST"])
@log_request
@require_discord_id
def uncheck_item():
    """
    Remove completion mark from an item
    ---
    tags: [Daily Checklist]
    parameters:
      - in: header
        name: X-Discord-Id
        required: true
        type: string
        description: Discord user ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            position:
              type: integer
              description: The position of the item to uncheck (1-based)
              example: 1
          required:
            - position
    responses:
      200:
        description: Item unchecked
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
    """
    discord_id = int(request.headers["X-Discord-Id"])
    data = request.get_json()
    position = data.get("position")
    if not position:
        return log_and_send_json_response({"status": "error", "message": "Missing position"}, status_code=400)
    success, msg = daily_checklist.uncheck_item(discord_id, position)
    return log_and_send_json_response({"status": "success" if success else "error", "message": msg})


@daily_checklist_bp.route("/edit", methods=["POST"])
@log_request
@require_discord_id
def edit_item():
    """
    Edit an item in your checklist
    ---
    tags: [Daily Checklist]
    parameters:
      - in: header
        name: X-Discord-Id
        required: true
        type: string
        description: Discord user ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            position:
              type: integer
              description: The position of the item to edit (1-based)
              example: 1
            new_item:
              type: string
              description: The new item text
              example: Do daily cleaning
          required:
            - position
            - new_item
    responses:
      200:
        description: Item edited
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
    """
    discord_id = int(request.headers["X-Discord-Id"])
    data = request.get_json()
    position = data.get("position")
    new_item = data.get("new_item")
    if not position or not new_item:
        return log_and_send_json_response({"status": "error", "message": "Missing position or new_item"}, status_code=400)
    success, msg = daily_checklist.edit_item(discord_id, position, new_item)
    return log_and_send_json_response({"status": "success" if success else "error", "message": msg})


@daily_checklist_bp.route("/move", methods=["POST"])
@log_request
@require_discord_id
def move_item():
    """
    Move an item to a different position
    ---
    tags: [Daily Checklist]
    parameters:
      - in: header
        name: X-Discord-Id
        required: true
        type: string
        description: Discord user ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            old_position:
              type: integer
              description: The current position of the item (1-based)
              example: 3
            new_position:
              type: integer
              description: The new position for the item (1-based)
              example: 1
          required:
            - old_position
            - new_position
    responses:
      200:
        description: Item moved
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
    """
    discord_id = int(request.headers["X-Discord-Id"])
    data = request.get_json()
    old_position = data.get("old_position")
    new_position = data.get("new_position")
    if not old_position or not new_position:
        return log_and_send_json_response({"status": "error", "message": "Missing old_position or new_position"}, status_code=400)
    success, msg = daily_checklist.move_item(discord_id, old_position, new_position)
    return log_and_send_json_response({"status": "success" if success else "error", "message": msg})


@daily_checklist_bp.route("/history", methods=["GET"])
@log_request
@require_discord_id
def history():
    """
    View your checklist for a specific date
    ---
    tags: [Daily Checklist]
    parameters:
      - in: header
        name: X-Discord-Id
        required: true
        schema:
          type: string
        description: Discord user ID
      - in: query
        name: date
        required: false
        schema:
          type: string
        description: Date in YYYY-MM-DD format
    responses:
      200:
        description: Checklist for the date
        schema:
          type: object
          properties:
            status:
              type: string
            items:
              type: array
              items:
                type: object
            message:
              type: string
    """
    discord_id = int(request.headers["X-Discord-Id"])
    date_str = request.args.get("date")
    try:
        if date_str:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            target_date = daily_checklist.get_current_day()
    except ValueError:
        return log_and_send_json_response({"status": "error", "message": "Invalid date format. Please use YYYY-MM-DD"}, status_code=400)
    items = daily_checklist.get_checklist_for_date(discord_id, target_date)
    response = daily_checklist.format_checklist_response(items, target_date)
    serialized_items = [{"item": item.item, "position": item.sort_order, "checked": checked} for item, checked in items]
    return log_and_send_json_response({"status": "success", "items": serialized_items, "message": response})
