from flask import Blueprint, request

from shared.dice import dice_roll_command, random_command
from shared.log import log_and_send_json_response, log_request

dice_bp = Blueprint("dice", __name__, url_prefix="/api/dice")


@dice_bp.route("/roll", methods=["GET"])
@log_request
def roll_dice():
    """
    Roll dice using standard dice notation (e.g., 1d20, 2d6+3).
    ---
    tags:
      - dice
    parameters:
      - name: args
        in: query
        type: string
        required: true
        description: Dice roll arguments, space-separated (e.g., 1d20 or 2d6 + 3)
    responses:
      200:
        description: Dice roll result
        schema:
          type: object
          properties:
            result:
              type: string
              example: (4 + 5) + 3 = 12
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
              example: Invalid input. please use !r {num}d{num} ie. `!r 1d20`
    """
    args = request.args.get("args")
    if not args:
        return log_and_send_json_response({"error": "Missing required parameter: args"}, status_code=400)
    try:
        # Split by spaces for multiple arguments
        result = dice_roll_command(args.split())
    except Exception as e:
        return log_and_send_json_response({"error": str(e)}, status_code=400)
    return log_and_send_json_response({"result": result})


@dice_bp.route("/random", methods=["GET"])
@log_request
def random_number():
    """
    Generate a random number between two values (inclusive for integers).
    ---
    tags:
      - dice
    parameters:
      - name: min
        in: query
        type: number
        required: true
        description: Minimum value
      - name: max
        in: query
        type: number
        required: true
        description: Maximum value
    responses:
      200:
        description: Random number result
        schema:
          type: object
          properties:
            result:
              type: string
              example: 42
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
              example: Invalid input. Please use random <min> <max>
    """
    min_val = request.args.get("min")
    max_val = request.args.get("max")
    if min_val is None or max_val is None:
        return log_and_send_json_response({"error": "Missing required parameters: min and max"}, status_code=400)
    try:
        result = random_command([min_val, max_val])
    except Exception as e:
        return log_and_send_json_response({"error": str(e)}, status_code=400)
    return log_and_send_json_response({"result": result})
