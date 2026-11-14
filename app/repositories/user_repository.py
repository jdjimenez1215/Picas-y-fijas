from abc import ABC, abstractmethod
from typing import Optional
from app.domain.user import User


class UserRepository(ABC):
    """Contrato de almacenamiento de usuarios."""

    @abstractmethod
    def save(self, user: User) -> None:
        """Guarda o actualiza un usuario."""
        ...

    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]:
        """Devuelve el usuario o None si no existe."""
        ...