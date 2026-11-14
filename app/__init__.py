from flask import Flask
from werkzeug.exceptions import HTTPException

from app.repositories.memory_game_repository import MemoryGameRepository
from app.repositories.memory_user_repository import MemoryUserRepository
from app.services.auth_service import AuthService
from app.services.game_service import GameService

from app.domain.exceptions import (
    DomainError,
    NotFoundError,
    UnauthorizedError,
)

from app.routes.auth_routes import auth_bp
from app.routes.game_routes import game_bp


def create_app(secret_key: str = "clave-de-desarrollo") -> Flask:
    """
    Factory de la app Flask.
    Aqui se ensambla TODO: repositorios, servicios, blueprints y handlers de error.
    """
    app = Flask(__name__)

    # ---------- Composition Root ----------
    user_repo = MemoryUserRepository()
    game_repo = MemoryGameRepository()
    auth_service = AuthService(user_repo, secret_key=secret_key)
    game_service = GameService(game_repo)

    app.config["AUTH_SERVICE"] = auth_service
    app.config["GAME_SERVICE"] = game_service

    # ---------- Rutas ----------
    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)

    # ---------- Errores de DOMINIO -> HTTP ----------
    @app.errorhandler(NotFoundError)
    def handle_not_found(e):
        return {"error": str(e)}, 404

    @app.errorhandler(UnauthorizedError)
    def handle_unauthorized(e):
        return {"error": str(e)}, 401

    @app.errorhandler(DomainError)
    def handle_domain(e):
        return {"error": str(e)}, 400

    @app.errorhandler(ValueError)
    def handle_value(e):
        return {"error": str(e)}, 400

    # ---------- Errores HTTP genericos -> JSON ----------
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        # Atrapa 404 (ruta no existe), 405 (metodo no permitido), etc.
        # y responde en JSON para mantener consistencia REST.
        return {"error": e.name, "description": e.description}, e.code

    return app
