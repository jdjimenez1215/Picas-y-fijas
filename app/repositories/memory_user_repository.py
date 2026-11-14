from typing import Optional
from app.domain.user import User
from app.repositories.user_repository import UserRepository


class MemoryUserRepository(UserRepository):
    """Implementación en memoria del repositorio de usuarios."""

    def __init__(self):
        self._users: dict[str, User] = {}   # clave = username

    def save(self, user: User) -> None:
        self._users[user.username] = user

    def find_by_username(self, username: str) -> Optional[User]:
        return self._users.get(username)