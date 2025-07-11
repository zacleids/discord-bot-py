import asyncio

from flask import Blueprint, request

from shared.eight_ball import eight_ball, f_in_chat, gg
from shared.log import log_and_send_json_response, log_request

eight_ball_bp = Blueprint("eight_ball", __name__, url_prefix="/api/eight_ball")


@eight_ball_bp.route("/ask", methods=["GET"])
@log_request
def ask_eight_ball():
    """
    Ask the magic eight ball a question.
    ---
    tags:
      - eight_ball
    parameters:
      - name: message
        in: query
        type: string
        required: true
        description: The question or message to ask the eight ball
    responses:
      200:
        description: Eight ball response
        schema:
          type: object
          properties:
            result:
              type: string
              example: Yes, definitely.
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Missing required parameter: message"
    """
    message = request.args.get("message")
    if not message:
        return log_and_send_json_response({"error": "Missing required parameter: message"}, status_code=400)
    try:
        result = asyncio.run(eight_ball(message.split()))
    except Exception as e:
        return log_and_send_json_response({"error": str(e)}, status_code=400)
    return log_and_send_json_response({"result": result})


@eight_ball_bp.route("/f", methods=["GET"])
@log_request
def f_in_chat_route():
    """
    Press F to pay respects.
    ---
    tags:
      - eight_ball
    responses:
      200:
        description: F in the chat response
        schema:
          type: object
          properties:
            result:
              type: string
              example: F
    """
    result = asyncio.run(f_in_chat())
    return log_and_send_json_response({"result": result})


@eight_ball_bp.route("/gg", methods=["GET"])
@log_request
def gg_route():
    """
    Good Game!
    ---
    tags:
      - eight_ball
    responses:
      200:
        description: GG response
        schema:
          type: object
          properties:
            result:
              type: string
              example: GG WP
    """
    result = gg()
    return log_and_send_json_response({"result": result})
