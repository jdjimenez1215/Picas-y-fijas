from flask import Blueprint, request, current_app, jsonify

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    """POST /login  ->  {"token": "..."}"""
    data = request.get_json(silent=True) or {}
    username = data.get("username")

    auth_service = current_app.config["AUTH_SERVICE"]
    token = auth_service.login(username)

    return jsonify({"token": token}), 200
