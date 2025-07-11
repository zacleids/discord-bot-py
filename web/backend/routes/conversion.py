from flask import Blueprint, request

from shared import conversion
from shared.log import log_and_send_json_response, log_request

conversion_bp = Blueprint("conversion", __name__, url_prefix="/api/conversion")


@conversion_bp.route("/convert", methods=["GET"])
@log_request
def convert():
    """
    Convert between units (length, mass, volume).
    ---
    tags:
      - conversion
    parameters:
      - name: from_unit
        in: query
        type: string
        required: true
        enum:
          - METER
          - KILOMETER
          - CENTIMETER
          - MILLIMETER
          - MILE
          - YARD
          - FOOT
          - INCH
          - GRAM
          - KILOGRAM
          - POUND
          - OUNCE
          - LITER
          - MILLILITER
          - GALLON
          - QUART
          - PINT
          - FLUID_OUNCE
          - CELSIUS
          - FAHRENHEIT
          - KELVIN
          - METER_PER_SECOND
          - KILOMETER_PER_HOUR
          - MILE_PER_HOUR
        description: The unit to convert from
      - name: to_unit
        in: query
        type: string
        required: true
        enum:
          - METER
          - KILOMETER
          - CENTIMETER
          - MILLIMETER
          - MILE
          - YARD
          - FOOT
          - INCH
          - GRAM
          - KILOGRAM
          - POUND
          - OUNCE
          - LITER
          - MILLILITER
          - GALLON
          - QUART
          - PINT
          - FLUID_OUNCE
          - CELSIUS
          - FAHRENHEIT
          - KELVIN
          - METER_PER_SECOND
          - KILOMETER_PER_HOUR
          - MILE_PER_HOUR
        description: The unit to convert to
      - name: number
        in: query
        type: number
        required: true
        description: The value to convert
    responses:
      200:
        description: Conversion result
        schema:
          type: object
          properties:
            result:
              type: string
              example: 150 Kilometers = 93.2059 Miles
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
              example: Invalid unit or value
    """
    from_unit = request.args.get("from_unit")
    to_unit = request.args.get("to_unit")
    number = request.args.get("number")
    if not from_unit or not to_unit or number is None:
        return log_and_send_json_response({"error": "Missing required parameters"}, status_code=400)
    try:
        from_unit_enum = conversion.UnitType[from_unit.upper()]
        to_unit_enum = conversion.UnitType[to_unit.upper()]
    except KeyError:
        return log_and_send_json_response({"error": "Invalid unit"}, status_code=400)
    try:
        number = float(number)
    except ValueError:
        return log_and_send_json_response({"error": "Invalid number"}, status_code=400)
    try:
        result = conversion.get_conversion_display(from_unit_enum, to_unit_enum, number)
    except Exception as e:
        return log_and_send_json_response({"error": str(e)}, status_code=400)
    return log_and_send_json_response({"result": result})
