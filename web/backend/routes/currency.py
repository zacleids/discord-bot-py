from flask import Blueprint, request

from shared import currency
from shared.log import log_and_send_json_response, log_request
from shared.utils import format_number

# from web.backend.middleware import require_discord_id

currency_bp = Blueprint("currency", __name__, url_prefix="/api/currency")

CURRENCY_CODES = list(currency.CURRENCY_NAMES.keys())


@currency_bp.route("/convert", methods=["GET"])
@log_request
# @require_discord_id
def convert_currency():
    """
    Convert between currencies.
    ---
    tags:
      - currency
    parameters:
      - name: from_currency
        in: query
        type: string
        required: true
        enum:
          - USD
          - MXN
          - CAD
          - EUR
          - GBP
          - JPY
          - AUD
          - ILS
          - INR
          - BRL
          - ARS
          - VES
          - PEN
          - SGD
          - CHF
          - HKD
          - KRW
          - CNY
          - SEK
          - NOK
          - NZD
          - PHP
          - TWD
        description: The currency code to convert from
      - name: to_currency
        in: query
        type: string
        required: true
        enum:
          - USD
          - MXN
          - CAD
          - EUR
          - GBP
          - JPY
          - AUD
          - ILS
          - INR
          - BRL
          - ARS
          - VES
          - PEN
          - SGD
          - CHF
          - HKD
          - KRW
          - CNY
          - SEK
          - NOK
          - NZD
          - PHP
          - TWD
        description: The currency code to convert to
      - name: amount
        in: query
        type: number
        required: true
        description: The amount to convert
    responses:
      200:
        description: Conversion result
        schema:
          type: object
          properties:
            result:
              type: string
              example: 100 USD = 92.34 EUR
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
              example: Invalid currency code or amount
    """
    from_currency_code = request.args.get("from_currency")
    to_currency_code = request.args.get("to_currency")
    amount = request.args.get("amount")
    if not from_currency_code or not to_currency_code or amount is None:
        return log_and_send_json_response({"error": "Missing required parameters"}, status_code=400)
    if from_currency_code not in CURRENCY_CODES or to_currency_code not in CURRENCY_CODES:
        return log_and_send_json_response({"error": "Invalid currency code"}, status_code=400)
    try:
        amount = float(amount)
    except ValueError:
        return log_and_send_json_response({"error": "Invalid amount"}, status_code=400)
    try:
        result = currency.convert_currency(from_currency_code, to_currency_code, amount)
        formatted = f"{format_number(amount)} {from_currency_code} = {format_number(result)} {to_currency_code}"
    except Exception as e:
        return log_and_send_json_response({"error": str(e)}, status_code=400)
    return log_and_send_json_response({"result": formatted})
