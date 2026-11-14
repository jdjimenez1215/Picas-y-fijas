from app.repositories.memory_game_repository import MemoryGameRepository
from app.repositories.memory_user_repository import MemoryUserRepository
from app.domain.game import Game
from app.domain.user import User


def main():
    # 1. Creamos las implementaciones concretas (los "asistentes")
    game_repo = MemoryGameRepository()
    user_repo = MemoryUserRepository()

    # 2. Las usamos como si fueran GameRepository / UserRepository
    #    (polimorfismo, LSP, DIP funcionando)
    user_repo.save(User(username="ana", password_hash="hash123"))
    game_repo.save(Game(id="p-1", secret="4271", creator="ana"))

    # 3. Consultamos
    print(user_repo.find_by_username("ana"))          # User(...)
    print(game_repo.find_by_id("p-1").to_dict())      # dict de la partida
    print(len(game_repo.find_all()))                  # 1


if __name__ == "__main__":
    main()