from flask import Blueprint, current_app, g, jsonify, request, url_for

from app.routes.decorators import require_auth

game_bp = Blueprint("game", __name__, url_prefix="/juego")


def _json_object():
    data = request.get_json()
    if not isinstance(data, dict):
        raise ValueError("El cuerpo debe ser un objeto JSON")
    return data


@game_bp.post("")
@require_auth
def create_game():
    data = _json_object()
    game = current_app.config["GAME_SERVICE"].create_game(g.username, data.get("number"))
    return jsonify(game.to_dict()), 201, {"Location": url_for(".get_game", game_id=game.id)}


@game_bp.put("/<game_id>")
@require_auth
def join_game(game_id):
    data = _json_object()
    if data.get("username") != g.username:
        raise ValueError("username debe coincidir con el usuario del token")
    game = current_app.config["GAME_SERVICE"].join_game(game_id, g.username, data.get("number"))
    return jsonify(game.to_dict())


@game_bp.post("/<game_id>/jugar")
@require_auth
def play(game_id):
    data = _json_object()
    result = current_app.config["GAME_SERVICE"].play(game_id, g.username, data.get("number"))
    return jsonify(result)


@game_bp.get("/<game_id>")
@require_auth
def get_game(game_id):
    game = current_app.config["GAME_SERVICE"].get_game(game_id, g.username)
    return jsonify(game.to_dict())


@game_bp.get("")
@require_auth
def list_games():
    games = current_app.config["GAME_SERVICE"].list_games()
    return jsonify([
        {key: value for key, value in game.to_dict().items()
         if key in {"id", "creator", "players", "status", "winner"}}
        for game in games
    ])
