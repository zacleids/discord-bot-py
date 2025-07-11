from flask import Blueprint, request

from shared.encode import encode_decode
from shared.log import log_and_send_json_response, log_request

encode_bp = Blueprint("encode", __name__, url_prefix="/api/encode")


@encode_bp.route("/encode", methods=["GET"])
@log_request
def encode_route():
    """
    Encode a message using the selected encoder.
    ---
    tags:
      - encode
    parameters:
      - name: message
        in: query
        type: string
        required: true
        description: The message to encode
      - name: encoder
        in: query
        type: string
        required: true
        enum:
          - base64
          - binary
          - morse
          - rot13
        description: The encoder to use
    responses:
      200:
        description: Encoded result
        schema:
          type: object
          properties:
            result:
              type: string
              example: SGVsbG8gd29ybGQh
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Missing required parameter: message or encoder"
    """
    message = request.args.get("message")
    encoder = request.args.get("encoder")
    if not message or not encoder:
        return log_and_send_json_response({"error": "Missing required parameter: message or encoder"}, status_code=400)
    try:
        result = encode_decode(message, encoder, "encode")
    except Exception as e:
        return log_and_send_json_response({"error": str(e)}, status_code=400)
    return log_and_send_json_response({"result": result})


@encode_bp.route("/decode", methods=["GET"])
@log_request
def decode_route():
    """
    Decode a message using the selected encoder.
    ---
    tags:
      - encode
    parameters:
      - name: message
        in: query
        type: string
        required: true
        description: The message to decode
      - name: encoder
        in: query
        type: string
        required: true
        enum:
          - base64
          - binary
          - morse
          - rot13
        description: The encoder to use
    responses:
      200:
        description: Decoded result
        schema:
          type: object
          properties:
            result:
              type: string
              example: Hello world!
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Missing required parameter: message or encoder"
    """
    message = request.args.get("message")
    encoder = request.args.get("encoder")
    if not message or not encoder:
        return log_and_send_json_response({"error": "Missing required parameter: message or encoder"}, status_code=400)
    try:
        result = encode_decode(message, encoder, "decode")
    except Exception as e:
        return log_and_send_json_response({"error": str(e)}, status_code=400)
    return log_and_send_json_response({"result": result})
