from functools import wraps

from flask import jsonify, request


def require_discord_id(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        discord_id = request.headers.get("X-Discord-Id")
        if not discord_id:
            return jsonify({"error": "Missing X-Discord-Id header"}), 400
        # Optionally, you can attach discord_id to kwargs or flask.g here
        return f(*args, **kwargs)

    return decorated_function
