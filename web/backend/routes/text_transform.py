from flask import Blueprint, request

from shared.log import log_and_send_json_response, log_request
from shared.text_transform import TransformChoice, transform_text

text_transform_bp = Blueprint("text_transform", __name__, url_prefix="/api/text_transform")


@text_transform_bp.route("/transform", methods=["GET"])
@log_request
def transform_route():
    """
    Transform text in various ways (alternating_case, mirror, reverse, upside_down).
    ---
    tags:
      - text_transform
    parameters:
      - name: text
        in: query
        type: string
        required: true
        description: The text to transform
      - name: type
        in: query
        type: string
        required: true
        enum:
          - alternating_case
          - mirror
          - reverse
          - upside_down
        description: The type of transformation
    responses:
      200:
        description: Transformed text
        schema:
          type: object
          properties:
            result:
              type: string
              example: ¡plɹoM ollǝH
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Missing required parameter: text or type"
    """
    text = request.args.get("text")
    transform_type = request.args.get("type")
    if not text or not transform_type:
        return log_and_send_json_response({"error": "Missing required parameter: text or type"}, status_code=400)
    try:
        enum_type = TransformChoice(transform_type)
        result = transform_text(text, enum_type)
    except ValueError:
        valid_types = ", ".join([t.value for t in TransformChoice])
        return log_and_send_json_response({"error": f"Invalid transform type. Valid types: {valid_types}"}, status_code=400)
    except Exception as e:
        return log_and_send_json_response({"error": str(e)}, status_code=400)
    return log_and_send_json_response({"result": result})
