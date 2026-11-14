import random
import uuid
from typing import List

from app.domain.game import Game
from app.domain.exceptions import NotFoundError
from app.repositories.game_repository import GameRepository


class GameService:
 
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo

    def create_game(self, creator: str) -> Game:
        """Crea una partida nueva con secreto aleatorio unico de 4 digitos."""
        game_id = str(uuid.uuid4())
        secret = self._generate_secret()
        game = Game(id=game_id, secret=secret, creator=creator)
        self.game_repo.save(game)
        return game

    def join_game(self, game_id: str, player: str) -> Game:
        """Une un jugador a la partida. Lanza NotFoundError si no existe."""
        game = self._get_or_raise(game_id)
        game.join(player)
        self.game_repo.save(game)
        return game

    def play(self, game_id: str, player: str, guess: str) -> dict:
        """Procesa un intento. Devuelve {fijas, picas}."""
        game = self._get_or_raise(game_id)
        result = game.evaluate(player, guess)
        self.game_repo.save(game)
        return result

    def get_game(self, game_id: str) -> Game:
        return self._get_or_raise(game_id)

    def list_games(self) -> List[Game]:
        return self.game_repo.find_all()

    def _get_or_raise(self, game_id: str) -> Game:
        game = self.game_repo.find_by_id(game_id)
        if game is None:
            raise NotFoundError(f"No existe una partida con id '{game_id}'")
        return game

    def _generate_secret(self) -> str:
        """4 digitos unicos, generados con aleatoriedad criptografica."""
        return "".join(random.SystemRandom().sample("0123456789", 4))
