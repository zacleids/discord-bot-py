from flask import Blueprint, request

from shared.log import log_and_send_json_response, log_request
from shared.rps import play_rock_paper_scissors

rps_bp = Blueprint("rps", __name__, url_prefix="/api/rps")


@rps_bp.route("/play", methods=["GET"])
@log_request
def play_rps():
    """
    Play Rock, Paper, Scissors against the bot.
    ---
    tags:
      - rps
    parameters:
      - name: choice
        in: query
        type: string
        required: true
        enum:
          - rock
          - paper
          - scissors
        description: Your choice (rock, paper, or scissors)
    responses:
      200:
        description: RPS result
        schema:
          type: object
          properties:
            result:
              type: string
              example: You chose rock. I chose paper. You lose!
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid input. please use choose rock, paper, or scissors"
    """
    choice = request.args.get("choice")
    if not choice:
        return log_and_send_json_response({"error": "Missing required parameter: choice"}, status_code=400)
    try:
        result = play_rock_paper_scissors([choice])
        # Remove Discord markdown for web output
        result = result.replace("**", "")
    except Exception as e:
        return log_and_send_json_response({"error": str(e)}, status_code=400)
    return log_and_send_json_response({"result": result})
