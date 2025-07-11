from functools import wraps

from flask import request

from shared.log import log_and_send_json_response


def require_discord_id(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Try to get Discord ID from OAuth token (future)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return log_and_send_json_response({"error": "Bearer tokens not implemented "}, status_code=501)

            # token = auth_header.split(" ", 1)[1]
            # Validate token and extract discord_id here (call Discord API or verify JWT)
            # discord_id = get_discord_id_from_token(token)
        else:
            # 2. Fallback to X-Discord-Id header (current)
            discord_id = request.headers.get("X-Discord-Id")
            if not discord_id or discord_id.strip() == "" or discord_id.strip().lower() == "null":
                return log_and_send_json_response({"error": "Missing or invalid X-Discord-Id header"}, status_code=400)
            try:
                discord_id_int = int(discord_id)
                if discord_id_int <= 0:
                    raise ValueError
            except Exception:
                return log_and_send_json_response({"error": "X-Discord-Id header must be a valid Discord user ID"}, status_code=400)
        return f(*args, **kwargs)

    return decorated_function
