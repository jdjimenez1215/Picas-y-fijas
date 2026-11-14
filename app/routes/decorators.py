from functools import wraps

from flask import request, current_app, g

from app.domain.exceptions import UnauthorizedError


def require_auth(f):
    """
    Decorador que:
      1. Extrae el token del header Authorization: Bearer <token>
      2. Lo valida con AuthService.verify_token
      3. Deja el username en g.username para que la ruta lo use

    STATELESS: cada request debe traer su propio token.
    El servidor NO recuerda quien eres entre requests.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            raise UnauthorizedError("Falta el header Authorization: Bearer <token>")

        token = auth_header[len("Bearer "):]

        auth_service = current_app.config["AUTH_SERVICE"]
        username = auth_service.verify_token(token)

        # Guardar el username en el contexto del request actual
        g.username = username

        return f(*args, **kwargs)

    return wrapper
