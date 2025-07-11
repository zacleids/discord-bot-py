from flask import Blueprint, request

from shared import coin
from shared.log import log_and_send_json_response, log_request

coin_bp = Blueprint("coin", __name__, url_prefix="/api/coin")


@coin_bp.route("/flip", methods=["GET"])
@log_request
def coinflip():
    """
    Flip a coin.
    ---
    tags:
      - coin
    responses:
      200:
        description: Result of the coin flip
        schema:
          type: object
          properties:
            result:
              type: string
              example: heads
    """
    result = coin.flip_coin()
    return log_and_send_json_response({"result": result})


@coin_bp.route("/flip_n", methods=["GET"])
@log_request
def coinflip_n():
    """
    Flip N coins.
    ---
    tags:
      - coin
    parameters:
      - name: n
        in: query
        type: integer
        required: false
        default: 1
        description: Number of coins to flip (1-100000)
    responses:
      200:
        description: Result of flipping N coins
        schema:
          type: object
          properties:
            result:
              type: string
              examples:
                short:
                  summary: Short result for n < 25
                  value: HTTHTHTTH
                summary:
                  summary: Summary result for n >= 25
                  value: |
                    Heads: 5
                    Tails: 5
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
              example: n must be between 1 and 100000
    """
    try:
        n = int(request.args.get("n", 1))
        if n < 1 or n > 100000:
            return log_and_send_json_response({"error": "n must be between 1 and 100000"}, status_code=400)
    except (TypeError, ValueError):
        return log_and_send_json_response({"error": "Invalid n parameter"}, status_code=400)
    result = coin.flip_coins([str(n)])
    return log_and_send_json_response({"result": result})
