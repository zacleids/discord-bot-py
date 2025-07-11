from flasgger import Swagger
from flask import Flask, jsonify

from .routes.coin import coin_bp
from .routes.conversion import conversion_bp
from .routes.currency import currency_bp
from .routes.daily_checklist import daily_checklist_bp
from .routes.dice import dice_bp
from .routes.eight_ball import eight_ball_bp
from .routes.encode import encode_bp
from .routes.rps import rps_bp
from .routes.text_transform import text_transform_bp

app = Flask(__name__)
app.register_blueprint(coin_bp)
app.register_blueprint(conversion_bp)
app.register_blueprint(currency_bp)
app.register_blueprint(daily_checklist_bp)
app.register_blueprint(dice_bp)
app.register_blueprint(eight_ball_bp)
app.register_blueprint(encode_bp)
app.register_blueprint(rps_bp)
app.register_blueprint(text_transform_bp)
Swagger(app)


@app.route("/")
def index():
    return jsonify({"message": "Hello from Flask backend!"})


if __name__ == "__main__":
    app.run(debug=True)
