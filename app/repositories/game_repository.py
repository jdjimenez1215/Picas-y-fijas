from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.game import Game


class GameRepository(ABC):
  

    @abstractmethod
    def save(self, game: Game) -> None:
        """Guarda o actualiza una partida."""
        ...

    @abstractmethod
    def find_by_id(self, game_id: str) -> Optional[Game]:
        """Devuelve la partida o None si no existe."""
        ...

    @abstractmethod
    def find_all(self) -> List[Game]:
        """Devuelve todas las partidas."""
        ...