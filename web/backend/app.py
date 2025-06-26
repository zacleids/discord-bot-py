from flask import Flask, jsonify

from shared import coin
from shared.log import log_and_send_json_response, log_request

from .middleware import require_discord_id

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({"message": "Hello from Flask backend!"})


@app.route("/api/coinflip", methods=["GET"])
@log_request
@require_discord_id
def api_coinflip():
    result = coin.flip_coin()
    return log_and_send_json_response({"result": result})


if __name__ == "__main__":
    app.run(debug=True)
