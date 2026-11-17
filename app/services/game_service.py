import secrets
from typing import List

from app.domain.game import Game
from app.domain.exceptions import ForbiddenError, NotFoundError
from app.repositories.game_repository import GameRepository


class GameService:
 
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo

    def create_game(self, creator: str, secret: str) -> Game:
        """Crea una partida con el secreto del primer jugador."""
        game = Game(id=self._new_game_id(), secret=secret, creator=creator)
        self.game_repo.save(game)
        return game

    def _new_game_id(self) -> str:
        """Genera un id numérico de 6 dígitos distintos, único entre las partidas."""
        used = {game.id for game in self.game_repo.find_all()}
        # 9 * 9 * 8 * 7 * 6 * 5 = 136080 combinaciones posibles.
        if len(used) >= 136_080:
            raise RuntimeError("No quedan identificadores de partida disponibles")
        while True:
            game_id = self._candidate_game_id()
            if game_id not in used:
                return game_id

    @staticmethod
    def _candidate_game_id() -> str:
        """Número de 6 dígitos aleatorios, distintos y sin ceros a la izquierda."""
        first = secrets.choice("123456789")
        pool = [digit for digit in "0123456789" if digit != first]
        rest = [pool.pop(secrets.randbelow(len(pool))) for _ in range(5)]
        return first + "".join(rest)

    def join_game(self, game_id: str, player: str, secret: str) -> Game:
        """Une un jugador a la partida. Lanza NotFoundError si no existe."""
        game = self._get_or_raise(game_id)
        game.join(player, secret)
        self.game_repo.save(game)
        return game

    def play(self, game_id: str, player: str, guess: str) -> dict:
        """Procesa un intento. Devuelve {fijas, picas}."""
        game = self._get_or_raise(game_id)
        result = game.evaluate(player, guess)
        self.game_repo.save(game)
        return result

    def get_game(self, game_id: str, player: str) -> Game:
        game = self._get_or_raise(game_id)
        if player not in game.players:
            raise ForbiddenError("Solo los participantes pueden consultar esta partida")
        return game

    def list_games(self) -> List[Game]:
        return self.game_repo.find_all()

    def _get_or_raise(self, game_id: str) -> Game:
        game = self.game_repo.find_by_id(game_id)
        if game is None:
            raise NotFoundError(f"No existe una partida con id '{game_id}'")
        return game
