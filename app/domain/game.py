from enum import Enum
from typing import List, Optional 

class GameStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class Game:
    def __init__(self, id: str, secret: str, creator: str):
        self.id = id
        self.secret = secret
        self.creator = creator
        self.players: List[str] = [creator]
        self.attempts: List[dict] = []
        self.status: GameStatus = GameStatus.WAITING
        self.winner: Optional[str] = None

    def join(self, player: str) -> None:
        if self.status == GameStatus.FINISHED:
            raise ValueError("No se puede unir a una partida terminada")
        if player in self.players:
            raise ValueError(f"El jugador '{player}' ya está en la partida")
        self.players.append(player)
        if self.status == GameStatus.WAITING:
            self.status = GameStatus.IN_PROGRESS

    def evaluate(self, player: str, guess: str) -> dict:
        if self.status == GameStatus.FINISHED:
            raise ValueError("La partida ya terminó")
        if player not in self.players:
            raise ValueError(f"El jugador '{player}' no está en la partida")

        self._validate_guess(guess)

        fijas, picas = self._count_picas_y_fijas(guess)
        result = {
            "player": player,
            "guess": guess,
            "fijas": fijas,
            "picas": picas,
        }
        self.attempts.append(result)

        if self.status == GameStatus.WAITING:
            self.status = GameStatus.IN_PROGRESS

        if fijas == 4:
            self.status = GameStatus.FINISHED
            self.winner = player

        return result

    def _validate_guess(self, guess: str) -> None:
        if not isinstance(guess, str) or len(guess) != 4 or not guess.isdigit():
            raise ValueError("El intento debe ser un string de exactamente 4 dígitos")
        if len(set(guess)) != 4:
            raise ValueError("El intento no puede tener dígitos repetidos")

    def _count_picas_y_fijas(self, guess: str) -> tuple:
        fijas = sum(1 for g, s in zip(guess, self.secret) if g == s)
        total_matches = sum(1 for g in guess if g in self.secret)
        picas = total_matches - fijas
        return fijas, picas

    def to_dict(self, reveal_secret: bool = False) -> dict:
        data = {
            "id": self.id,
            "creator": self.creator,
            "players": self.players,
            "status": self.status.value,
            "attempts": self.attempts,
            "winner": self.winner,
        }
        if reveal_secret or self.status == GameStatus.FINISHED:
            data["secret"] = self.secret
        return data