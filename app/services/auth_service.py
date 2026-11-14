from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.domain.user import User
from app.domain.exceptions import UnauthorizedError, DomainError
from app.repositories.user_repository import UserRepository


class AuthService:
    
    def __init__(self, user_repo: UserRepository, secret_key: str, token_max_age: int = 3600):
        self.user_repo = user_repo
        self.secret_key = secret_key
        self.token_max_age = token_max_age
        self._serializer = URLSafeTimedSerializer(secret_key, salt="picas-y-fijas-auth")

    def login(self, username: str) -> str:
        """
        Identifica al usuario. Si no existe, lo registra.
        Devuelve un token firmado con el username dentro.
        """
        if not username or not isinstance(username, str):
            raise DomainError("username es obligatorio")

        # Registro automático si es la primera vez
        if self.user_repo.find_by_username(username) is None:
            self.user_repo.save(User(username=username))

        return self._serializer.dumps({"username": username})

    def verify_token(self, token: str) -> str:
        """Valida el token y devuelve el username. Lanza UnauthorizedError si falla."""
        try:
            data = self._serializer.loads(token, max_age=self.token_max_age)
        except SignatureExpired:
            raise UnauthorizedError("Token expirado")
        except BadSignature:
            raise UnauthorizedError("Token inválido")
        return data["username"]