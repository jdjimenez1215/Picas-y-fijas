from typing import List, Optional
from app.domain.game import Game
from app.repositories.game_repository import GameRepository


class MemoryGameRepository(GameRepository):

    def __init__(self):
        # El diccionario está ENCAPSULADO aquí.
        # Nadie fuera de esta clase lo ve. Ni el servicio, ni las rutas.
        self._games: dict[str, Game] = {}

    def save(self, game: Game) -> None:
        self._games[game.id] = game

    def find_by_id(self, game_id: str) -> Optional[Game]:
        return self._games.get(game_id)

    def find_all(self) -> List[Game]:
        return list(self._games.values())