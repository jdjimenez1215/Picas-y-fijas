from enum import Enum
from random import choice

from app.domain.exceptions import ForbiddenError


class GameStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class Game:
    def __init__(self, id: str, secret: str, creator: str):
        self._validate_number(secret)
        self.id = id
        self.creator = creator
        self.players = [creator]
        self._secrets = {creator: secret}
        self.attempts = []
        self.status = GameStatus.WAITING
        self.turn = None
        self.winner = None

    def join(self, player: str, secret: str) -> None:
        if self.status == GameStatus.FINISHED:
            raise ValueError("No puedes unirte: la partida ya terminó")
        if player in self.players:
            raise ValueError(f"El jugador '{player}' ya está en la partida")
        if self.status != GameStatus.WAITING:
            raise ValueError("La partida ya tiene dos jugadores")
        self._validate_number(secret)
        self.players.append(player)
        self._secrets[player] = secret
        self.turn = choice(self.players)
        self.status = GameStatus.IN_PROGRESS

    def evaluate(self, player: str, guess: str) -> dict:
        if player not in self.players:
            raise ForbiddenError("No perteneces a esta partida")
        if self.status != GameStatus.IN_PROGRESS:
            raise ValueError("La partida no está en juego")
        if self.turn != player:
            raise ForbiddenError("No es tu turno")
        self._validate_number(guess)

        first, second = self.players
        opponent = second if player == first else first
        secret = self._secrets[opponent]
        fijas = sum(digit == target for digit, target in zip(guess, secret))
        picas = sum(digit in secret for digit in guess) - fijas
        result = {"player": player, "guess": guess, "fijas": fijas, "picas": picas}

        if fijas == 4:
            self.status = GameStatus.FINISHED
            self.winner = player
            self.turn = None
        else:
            self.turn = opponent

        self.attempts.append(result)
        return result

    @staticmethod
    def _validate_number(number: str) -> None:
        if not isinstance(number, str) or len(number) != 4 or not number.isascii() or not number.isdigit():
            raise ValueError("El número debe ser una cadena de exactamente 4 dígitos del 0 al 9")
        if len(set(number)) != 4:
            raise ValueError("El número no puede tener dígitos repetidos")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "creator": self.creator,
            "players": list(self.players),
            "status": self.status.value,
            "turn": self.turn,
            "attempts": list(self.attempts),
            "winner": self.winner,
        }
