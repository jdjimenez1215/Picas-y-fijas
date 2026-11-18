# Código explicado — Picas y Fijas

> **Propósito:** recorrer **cada archivo del repositorio** y explicar qué hace, por qué está así y qué respuesta conviene dar en el **corte (API, Docker, RPC y Kubernetes)**.
>
> **Relación con los otros documentos:**
> - `01_teoria_api_docker_rpc_kubernetes.md` → teoría general y estudio.
> - `02_apunte_parcial.md` → plantillas y ejercicios.
> - `03_sustentacion_proyecto.md` → guion para defender el proyecto.
> - **Este documento → el código real, línea por línea, con los cuatro temas del corte y el enunciado siempre a la vista.**
>
> **Repo:** <https://github.com/jdjimenez1215/Picas-y-fijas> · **Rama:** `main` · **Commit revisado:** `4632770` · **Stack:** Python 3.12 + Flask 3.1 + Gunicorn + Kubernetes (Killercoda).

---

## Índice

1. [El enunciado como contrato](#1-el-enunciado-como-contrato)
2. [Mapa del repositorio](#2-mapa-del-repositorio)
3. [Recorrido archivo por archivo](#3-recorrido-archivo-por-archivo)
4. [Tema 1 — API (REST + JSON)](#4-tema-1--api-rest--json)
5. [Tema 2 — Docker](#5-tema-2--docker)
6. [Tema 3 — RPC](#6-tema-3--rpc)
7. [Tema 4 — Kubernetes](#7-tema-4--kubernetes)
8. [Flujo completo: una petición de punta a punta](#8-flujo-completo-una-petición-de-punta-a-punta)
9. [Preguntas del corte respondidas desde el código](#9-preguntas-del-corte-respondidas-desde-el-código)
10. [Checklist final y límites](#10-checklist-final-y-límites)

---

## 1. El enunciado como contrato

Antes de mirar código, conviene tener claro **qué pide el enunciado**, porque casi todas las decisiones del proyecto responden a él:

| Requisito del enunciado | Implementación en el código |
| --- | --- |
| Juego “Picas y Fijas” distribuido | Cliente (navegador) + servidor Flask + Pod en Kubernetes. |
| Número secreto de **4 dígitos, todos diferentes** | `Game._validate_number()` en `app/domain/game.py`. |
| Fijas = mismo dígito en la misma posición; picas = mismo dígito en otra posición | `Game.evaluate()` (fórmula con `zip` y `in`). |
| El primero en revelar el número del otro gana | `fijas == 4` → `status = FINISHED`, `winner = player`. |
| `POST /login` — iniciar, registra el nombre | `auth_routes.login()` + `AuthService.login()` (registro automático). |
| `POST /juego` — crear, valida el número | `game_routes.create_game()` + `GameService.create_game()`. |
| `PUT /juego/{ID}` — unirse, envía nombre y número | `game_routes.join_game()` + `Game.join()`. |
| `POST /juego/{ID}/jugar` — solo si es tu turno; turno aleatorio | `Game.evaluate()` + `choice(self.players)` en `Game.join()`. |
| `GET /juego/{ID}` — ver estado (sin completar / en juego / terminado y ganador) | `game_routes.get_game()` + `GameStatus`. |
| `GET /juego` — listar juegos, quién los inició | `game_routes.list_games()` (resumen reducido). |
| Validar entrada: texto, dígitos repetidos, 4 dígitos | `_validate_number()` + `ValueError` → `400`. |
| **RESTful con JSON** | Flask, `jsonify`, `request.get_json()`, `Content-Type: application/json`. |
| Cualquier lenguaje / framework | Python + Flask. |
| **No es necesaria BD** | Repositorios en memoria (`dict`). |
| **Front básico para probar** | `app/templates/index.html` (HTML + JS vanilla). |
| Entregado en git público y sustentado | Repositorio en GitHub + esta documentación. |
| **Debe permitir despliegue en Kubernetes (Killercoda)** | `killercoda/namespace.yaml`, `deployment.yaml`, `service.yaml`. |

**Frase clave para responder:** “El enunciado pide seis endpoints y tres estados; el proyecto los implementa con seis rutas en Flask y un `Enum` de tres valores, y separa las reglas del juego en el dominio para que el cumplimiento sea verificable.”

> **Detalle del ejemplo del enunciado:** secreto `4271`, intento `1234` → **1 fija y 2 picas**. Con la fórmula del código:
>
> | pos | intento | secreto | resultado |
> | --- | --- | --- | --- |
> | 0 | `1` | `4` | `1` está en el secreto → pica |
> | 1 | `2` | `2` | igual y en la misma posición → **fija** |
> | 2 | `3` | `7` | no está → nada |
> | 3 | `4` | `1` | `4` está en el secreto → pica |
>
> `fijas = 1`, `picas = 3 - 1 = 2`. Coincide exactamente con el enunciado.

---

## 2. Mapa del repositorio

```text
Picas-y-fijas/
├── run.py                       # arranque local
├── requirements.txt             # dependencias
├── README.md                    # ejecución + contrato de la API
├── .gitignore                   # excluye .venv, cachés, etc.
├── app/
│   ├── __init__.py              # create_app(): composition root
│   ├── domain/
│   │   ├── exceptions.py        # errores de negocio
│   │   ├── game.py              # Game, GameStatus: REGLAS DEL JUEGO
│   │   └── user.py              # User (dataclass)
│   ├── repositories/
│   │   ├── __init__.py          # vacío: marca el paquete
│   │   ├── game_repository.py   # contrato abstracto
│   │   ├── memory_game_repository.py
│   │   ├── user_repository.py   # contrato abstracto
│   │   └── memory_user_repository.py
│   ├── services/
│   │   ├── __init__.py          # vacío
│   │   ├── auth_service.py      # login + tokens firmados
│   │   └── game_service.py      # crear/unir/jugar/listar + IDs
│   ├── routes/
│   │   ├── auth_routes.py       # POST /login
│   │   ├── decorators.py        # require_auth
│   │   └── game_routes.py       # los 5 endpoints de /juego
│   └── templates/
│       └── index.html           # front completo (una sola página)
├── docs/                        # documentación (la que estás leyendo)
└── killercoda/
    ├── namespace.yaml
    ├── deployment.yaml
    ├── service.yaml
    └── KILLERCODA.md            # guía paso a paso
```

Los `__init__.py` que quedan (`repositories/` y `services/`) están **vacíos**: solo marcan el paquete. En el commit `4632770` se eliminaron los de `domain/` y `routes/`; Python 3 los trata como *namespace packages*, así que las importaciones `app.domain...` y `app.routes...` siguen funcionando. La lógica de arranque está en `app/__init__.py`.

**Arquitectura en capas** (el patrón más defendible del proyecto):

```text
Navegador (index.html)
   ↓ fetch + JSON + Bearer
Rutas (app/routes)        → solo HTTP
   ↓
Servicios (app/services)  → casos de uso
   ↓
Dominio (app/domain)      → reglas puras
   ↓
Repositorios (app/repositories) → almacenamiento
```

---

## 3. Recorrido archivo por archivo

### 3.1 `run.py` — punto de entrada local

```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=False)
```

| Línea | Explicación |
| --- | --- |
| `from app import create_app` | Importa la **app factory** definida en `app/__init__.py`. |
| `app = create_app()` | Construye la aplicación: repositorios, servicios, rutas y errores. |
| `host="0.0.0.0"` | Escucha en **todas las interfaces**. Si fuera `127.0.0.1`, no se podría acceder desde otro contenedor ni desde `port-forward`. |
| `debug=True` | Recarga automática y errores detallados. **Solo desarrollo**; en Kubernetes se usa Gunicorn. |
| `threaded=False` | Atiende **una petición a la vez**. Esto evita carreras sobre los diccionarios en memoria (ver §3.6 y §7). |

**Respuesta de examen:** “`run.py` es solo el punto de entrada local; la lógica está en `create_app`. El `0.0.0.0` es obligatorio dentro de contenedores y `threaded=False` serializa el acceso al estado en memoria.”

---

### 3.2 `requirements.txt` — dependencias

```text
blinker==1.9.0
click==8.5.1
Flask==3.1.3
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.4
Werkzeug==3.1.9
```

- **Flask**: framework web; trae `click`, `Jinja2`, `Werkzeug` y `blinker` como dependencias transitivas.
- **itsdangerous**: firma de tokens (`URLSafeTimedSerializer`).
- Las versiones están **fijadas** (`==`) para que la instalación sea reproducible.
- **Gunicorn no aparece aquí**: se instala en el arranque del Pod (`pip install ... gunicorn==23.0.0`).

**Respuesta de examen:** “Fijamos versiones para reproducibilidad; Gunicorn se añade en el despliegue porque solo se necesita en producción, no para `python -m run`.”

---

### 3.3 `app/__init__.py` — la app factory y el *composition root*

Es el archivo más importante para entender cómo se arma todo:

```python
def create_app(secret_key: str | None = None) -> Flask:
    app = Flask(__name__)
    secret_key = secret_key or os.environ.get("PICAS_SECRET_KEY") or os.urandom(32).hex()
```

**Prioridad de la clave de firma:**
1. Parámetro `secret_key` (útil en tests).
2. Variable de entorno `PICAS_SECRET_KEY` (en el despliegue actual **no está configurada**, así que cae a la tercera opción).
3. `os.urandom(32).hex()` → clave aleatoria al arrancar (se pierde al reiniciar).

```python
    # Composition Root
    user_repo = MemoryUserRepository()
    game_repo = MemoryGameRepository()
    auth_service = AuthService(user_repo, secret_key=secret_key)
    game_service = GameService(game_repo)

    app.config["AUTH_SERVICE"] = auth_service
    app.config["GAME_SERVICE"] = game_service
```

Aquí se decide **qué implementación concreta** se usa. Los servicios reciben la **interfaz** (`GameRepository`, `UserRepository`), no la clase concreta. Eso es **inyección de dependencias** / **inversión de dependencias**: mañana se puede cambiar `MemoryGameRepository` por `PostgresGameRepository` sin tocar dominio ni servicios.

Los servicios se guardan en `app.config` para que las rutas los consulten con `current_app.config["GAME_SERVICE"]`.

```python
    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)

    @app.get("/")
    def index():
        return render_template("index.html")
```

- `auth_bp` → `POST /login`.
- `game_bp` → prefijo `/juego` con sus cinco rutas.
- `GET /` sirve el front (HTML).

```python
    @app.before_request
    def redirect_game_page():
        if request.method != "GET" or request.endpoint not in {"game.list_games", "game.get_game"}:
            return
        if request.headers.get("Authorization"):
            return
        if request.accept_mimetypes.best_match(["application/json", "text/html"]) != "text/html":
            return
        game_id = request.view_args.get("game_id")
        fragment = f"/partidas/{game_id}" if game_id else "/partidas"
        response = redirect(url_for("index", _anchor=fragment))
        response.headers["Cache-Control"] = "no-store"
        return response
```

Este *hook* se añadió en el commit `4632770` para arreglar la **navegación por URL**: si un navegador pide `GET /juego` o `GET /juego/{id}` **sin token** y acepta HTML, se redirige a `/#/partidas` o `/#/partidas/{id}` para que el front (que usa el *hash*) abra esa vista. Si la petición trae `Authorization` o pide JSON (`Accept: application/json`), no redirige: sigue siendo una llamada normal de la API. El `Cache-Control: no-store` evita que se guarde en caché. Es una capa de **conveniencia para el navegador**, no un cambio en el contrato REST.

```python
    @app.errorhandler(NotFoundError)      → 404
    @app.errorhandler(UnauthorizedError)  → 401
    @app.errorhandler(ForbiddenError)     → 403
    @app.errorhandler(DomainError)        → 400
    @app.errorhandler(ValueError)         → 400
    @app.errorhandler(HTTPException)      → código de la excepción (405, 415, 404 de ruta…)
```

Cada handler devuelve `{"error": ...}` con el código correcto. El de `HTTPException` es importante: convierte los errores por defecto de Flask (HTML) en **JSON**, manteniendo consistencia REST.

**Respuesta de examen:** “`create_app` es el *composition root*: crea repositorios, servicios, registra blueprints y normaliza errores a JSON. Usar app factory permite crear apps con configuraciones distintas (por ejemplo, una clave de prueba en tests).”

---

### 3.4 `app/domain/exceptions.py` — errores de negocio

```python
class DomainError(Exception): ...          # base
class NotFoundError(DomainError): ...      # → 404
class UnauthorizedError(DomainError): ...  # → 401
class ForbiddenError(DomainError): ...     # → 403
```

Jerarquía simple: el dominio lanza excepciones **sin saber HTTP**; `app/__init__.py` las traduce a códigos. Por eso `ForbiddenError` se usa para “no es tu turno” y `UnauthorizedError` para token malo.

**Respuesta de examen:** “El dominio no importa Flask; lanza `DomainError` y sus hijos. La capa HTTP decide el código. Así se respeta la separación de capas.”

---

### 3.5 `app/domain/user.py` — modelo de usuario

```python
@dataclass
class User:
    username: str
```

Un dataclass mínimo: solo identifica al jugador. No hay contraseña por decisión de alcance académico (ver `AuthService`).

---

### 3.6 `app/domain/game.py` — el corazón del juego

#### Estados

```python
class GameStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
```

Hereda de `str`, por eso `status.value` se serializa directamente como `"waiting"` en JSON. Los tres estados del enunciado: **sin completar**, **en juego**, **terminado**.

#### Constructor

```python
def __init__(self, id: str, secret: str, creator: str):
    self._validate_number(secret)      # valida antes de guardar
    self.id = id
    self.creator = creator
    self.players = [creator]
    self._secrets = {creator: secret}  # privado por convención
    self.attempts = []
    self.status = GameStatus.WAITING
    self.turn = None
    self.winner = None
```

Puntos clave:
- Valida el número **antes** de crear nada.
- `_secrets` guarda los números de ambos jugadores, pero **nunca se serializa** (ver `to_dict`).
- Estado inicial `waiting`, sin turno (falta el segundo jugador).

#### `join()` — unirse y sortear el turno

```python
def join(self, player: str, secret: str) -> None:
    if self.status == GameStatus.FINISHED: ...
    if player in self.players: ...
    if self.status != GameStatus.WAITING: ...
    self._validate_number(secret)
    self.players.append(player)
    self._secrets[player] = secret
    self.turn = choice(self.players)   # ← turno aleatorio del enunciado
    self.status = GameStatus.IN_PROGRESS
```

Orden de validaciones (importante para respuestas): **terminada → duplicado → llena → número → agregar → sortear → en juego**. El sorteo usa `random.choice`, que cumple “el primero en jugar se escoge de forma aleatoria”.

> **Observación para sustentar:** `choice` es aleatorio pero no criptográfico; para el juego basta. Los IDs, en cambio, usan `secrets` porque se muestran públicamente.

#### `evaluate()` — jugar y contar picas/fijas

```python
def evaluate(self, player: str, guess: str) -> dict:
    if player not in self.players:            raise ForbiddenError(...)
    if self.status != GameStatus.IN_PROGRESS: raise ValueError(...)
    if self.turn != player:                   raise ForbiddenError(...)
    self._validate_number(guess)

    first, second = self.players
    opponent = second if player == first else first
    secret = self._secrets[opponent]
    fijas = sum(d == t for d, t in zip(guess, secret))
    picas = sum(d in secret for d in guess) - fijas
    result = {"player": player, "guess": guess, "fijas": fijas, "picas": picas}

    if fijas == 4:
        self.status = GameStatus.FINISHED
        self.winner = player
        self.turn = None
    else:
        self.turn = opponent

    self.attempts.append(result)
    return result
```

Detalles que el profesor suele preguntar:

| Pregunta | Respuesta desde el código |
| --- | --- |
| ¿Cómo cuenta las fijas? | `zip(guess, secret)` compara dígito a dígito en la **misma posición**. |
| ¿Cómo cuenta las picas? | Cuenta cuántos dígitos del intento **pertenecen** al secreto (`in secret`) y resta las fijas, para no contar dos veces las que ya son fijas. |
| ¿Por qué no se duplica un dígito? | Porque `_validate_number` exige los 4 dígitos distintos. |
| ¿Qué pasa si juega alguien ajeno? | `ForbiddenError` → `403`, **antes** de mirar el número. |
| ¿Qué pasa si no es su turno? | `ForbiddenError` → `403`. El enunciado pide “solo si es su turno”. |
| ¿Qué pasa si acierta las 4? | `FINISHED`, `winner`, `turn=None`; el enunciado dice que gana quien revela el número. |
| ¿Quién gana? | El que envía el intento: `player`. |
| ¿Se alternan los turnos? | Sí: `self.turn = opponent` tras cada intento fallido. |

`evaluate` **devuelve solo el resultado del intento**, no el estado completo; el front luego llama a `GET /juego/{id}` para ver turno, historial y ganador.

#### `_validate_number()` — validación del enunciado

```python
@staticmethod
def _validate_number(number: str) -> None:
    if not isinstance(number, str) or len(number) != 4 or not number.isascii() or not number.isdigit():
        raise ValueError("El número debe ser una cadena de exactamente 4 dígitos del 0 al 9")
    if len(set(number)) != 4:
        raise ValueError("El número no puede tener dígitos repetidos")
```

| Caso | Resultado |
| --- | --- |
| `"4271"` | ✔ válido |
| `"0123"` | ✔ válido (conserva el cero a la izquierda) |
| `"1123"` | ✘ repetido |
| `"123"` / `"12345"` | ✘ longitud |
| `"12a4"` | ✘ no dígito |
| `1234` (int) | ✘ no es string |
| `"１２３４"` (Unicode) | ✘ `isascii()` evita dígitos no ASCII |

**¿Por qué string y no int?** Porque `"0123"` como entero sería `123` y perdería el cero inicial; además se puede validar longitud exacta. Es una decisión directa del enunciado (“no tenga texto, dígitos repetidos, sean 4 dígitos”).

#### `to_dict()` — serialización segura

```python
return {
    "id", "creator", "players", "status",
    "turn", "attempts", "winner"
}
```

**No incluye `_secrets`.** Nadie puede leer el número del rival con `GET /juego/{id}`. Es una de las respuestas más importantas en el corte.

---

### 3.7 Repositorios — contratos e implementación en memoria

**Contrato** (`game_repository.py`):

```python
class GameRepository(ABC):
    @abstractmethod
    def save(self, game: Game) -> None: ...
    @abstractmethod
    def find_by_id(self, game_id: str) -> Optional[Game]: ...
    @abstractmethod
    def find_all(self) -> List[Game]: ...
```

**Implementación** (`memory_game_repository.py`):

```python
class MemoryGameRepository(GameRepository):
    def __init__(self):
        self._games: dict[str, Game] = {}   # encapsulado
    def save(self, game): self._games[game.id] = game
    def find_by_id(self, game_id): return self._games.get(game_id)
    def find_all(self): return list(self._games.values())
```

Lo mismo para usuarios (`UserRepository` / `MemoryUserRepository`, con `dict[str, User]` indexado por `username`).

**Por qué importa:**
- El diccionario está **encapsulado**: ni el servicio ni las rutas lo tocan.
- Es el **punto de extensión** hacia una BD: basta una nueva clase que cumpla el contrato.
- Al ser memoria, **reiniciar el proceso borra todo** y obliga a usar **1 worker / 1 réplica** (ver Kubernetes).

---

### 3.8 `app/services/auth_service.py` — tokens y registro

```python
serializer = URLSafeTimedSerializer(secret_key, salt="picas-y-fijas-auth")

def login(self, username):
    if not username or not isinstance(username, str):
        raise DomainError("username es obligatorio")
    if self.user_repo.find_by_username(username) is None:
        self.user_repo.save(User(username=username))
    return self._serializer.dumps({"username": username})

def verify_token(self, token):
    try:
        data = self._serializer.loads(token, max_age=self.token_max_age)  # 3600 s
    except SignatureExpired:
        raise UnauthorizedError("Token expirado")
    except BadSignature:
        raise UnauthorizedError("Token inválido")
    return data["username"]
```

- **Registro automático** cumple “registra el name del jugador” del enunciado.
- El token está **firmado, no cifrado**: el username es legible, pero no modificable sin la clave.
- `max_age=3600` → vigencia de **1 hora**.
- `salt` separa este uso de otros usos de `itsdangerous`.
- Es **stateless**: no hay tabla de sesiones; cada petición trae su token.

**Respuesta de examen:** “El token se verifica en cada request; por eso el servidor puede estar en varios Pods siempre que compartan la misma clave de firma (en el proyecto, un Secret).”

---

### 3.9 `app/services/game_service.py` — casos de uso e IDs

```python
def create_game(self, creator, secret):
    game = Game(id=self._new_game_id(), secret=secret, creator=creator)
    self.game_repo.save(game)
    return game
```

Generación del ID:

```python
def _new_game_id(self):
    used = {g.id for g in self.game_repo.find_all()}
    if len(used) >= 136_080:
        raise RuntimeError("No quedan identificadores...")
    while True:
        candidate = self._candidate_game_id()
        if candidate not in used:
            return candidate

def _candidate_game_id(self):
    first = secrets.choice("123456789")           # sin cero inicial
    pool = [d for d in "0123456789" if d != first]
    rest = [pool.pop(secrets.randbelow(len(pool))) for _ in range(5)]
    return first + "".join(rest)                  # 6 dígitos distintos
```

- `9 × 9 × 8 × 7 × 6 × 5 = 136.080` combinaciones.
- Usa `secrets` (aleatoriedad criptográfica) porque el ID es público.
- Verifica colisiones contra las partidas existentes.

Operaciones:

| Método | Hace |
| --- | --- |
| `create_game` | Crea `Game`, guarda, devuelve. |
| `join_game` | Busca (o `NotFoundError`), delega en `game.join`, guarda. |
| `play` | Busca, delega en `game.evaluate`, guarda. |
| `get_game` | Busca y exige que `player in game.players`, si no `ForbiddenError`. |
| `list_games` | `find_all()` para el lobby. |
| `_get_or_raise` | Centraliza el `404` para ID inexistente. |

---

### 3.10 `app/routes/decorators.py` — autenticación en cada petición

```python
def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise UnauthorizedError("Falta el header Authorization: Bearer <token>")
        token = auth_header[len("Bearer "):]
        username = current_app.config["AUTH_SERVICE"].verify_token(token)
        g.username = username
        return f(*args, **kwargs)
    return wrapper
```

- Exige el prefijo exacto `Bearer `.
- Verifica firma y vigencia → `401` si falla.
- Guarda `g.username` (contexto **de la petición**, no sesión).
- **Stateless**: el servidor no recuerda quién eres entre peticiones.

**Respuesta de examen:** “`401` es para autenticación (token ausente/inválido/vencido); `403` es para autorización (token válido pero no participas o no es tu turno).”

---

### 3.11 `app/routes/auth_routes.py` — `POST /login`

```python
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not isinstance(data, dict):
        raise ValueError("El cuerpo debe ser un objeto JSON")
    username = data.get("username")
    token = current_app.config["AUTH_SERVICE"].login(username)
    return jsonify({"token": token}), 200
```

- `request.get_json()` parsea el body; si el `Content-Type` no es JSON, Flask responde `415`.
- Si el.body no es objeto, `ValueError` → `400`.
- Devuelve `200` con `{"token": ...}`.

---

### 3.12 `app/routes/game_routes.py` — los cinco endpoints del juego

```python
game_bp = Blueprint("game", __name__, url_prefix="/juego")
```

| Ruta | Decorador | Cuerpo | Respuesta | Función del servicio |
| --- | --- | --- | --- | --- |
| `POST /juego` | `@require_auth` | `{"number":"4271"}` | `201` + `Location` | `create_game(g.username, ...)` |
| `PUT /juego/<game_id>` | `@require_auth` | `{"username":"luis","number":"0123"}` | `200` | `join_game(...)` |
| `POST /juego/<game_id>/jugar` | `@require_auth` | `{"number":"0134"}` | `200` | `play(...)` |
| `GET /juego/<game_id>` | `@require_auth` | — | `200` | `get_game(...)` |
| `GET /juego` | `@require_auth` | — | `200` | `list_games()` |

Detalles:

```python
def _json_object():
    data = request.get_json()
    if not isinstance(data, dict):
        raise ValueError("El cuerpo debe ser un objeto JSON")
    return data
```

Centraliza la lectura y validación del body.

```python
return jsonify(game.to_dict()), 201, {"Location": url_for(".get_game", game_id=game.id)}
```

`201 Created` con `Location` generado por `url_for` (no escrito a mano).

```python
if data.get("username") != g.username:
    raise ValueError("username debe coincidir con el usuario del token")
```

El servidor **no confía** en el `username` del body: lo compara con el del token.

```python
return jsonify([
    {k: v for k, v in game.to_dict().items()
     if k in {"id", "creator", "players", "status", "winner"}}
    for game in games
])
```

El listado del lobby es **reducido**: sin `attempts` ni `turn`, y por supuesto sin secretos.

---

### 3.13 `app/templates/index.html` — el front básico

Es una sola página con CSS y JavaScript embebidos.

**Funciones principales:**

| Función | Para qué |
| --- | --- |
| `api(url, method, body)` | `fetch` con `Content-Type` y `Authorization: Bearer`; lanza error si `!response.ok`. |
| `action(id, event, run)` | Envuelve los formularios, evita dobles envíos con `busy` y muestra errores en `#message`. |
| `renderLobby(games)` | Separa **Disponibles** (`status !== "finished"`) y **Terminadas** (`finished`). |
| `gameCard(game)` | Tarjeta con botón “Unirme” / “Acceder” / “Ver resultado”. |
| `show(game)` | Vista de partida: estado, turno, ganador, historial. |
| `startPolling()` | `setInterval(refreshRound, 2000)`. |
| `startLobbyPolling()` | `setInterval(refreshLobby, 2000)`. |
| `lobby()` / `openGame(id)` / `showInvitation(game)` | Navegación con `#/partidas/...`. |

**Detalles defensivos:**
- `busy` y `lobbyLoading` evitan peticiones simultáneas.
- `document.visibilityState !== "visible"` no consulta si la pestaña está oculta.
- `lastGames` evita repintar si el JSON no cambió.
- `textContent` en vez de `innerHTML` → previene XSS.
- `type="password"` para los números secretos.
- `logout` solo borra las variables JS (no revoca el token).

**Respuesta de examen:** “El enunciado pedía un front básico; se hizo sin frameworks, con `fetch` y polling de 2 s. Una alternativa sería WebSocket/SSE, pero añade reconexión y estado; para dos jugadores el polling es suficiente.”

---

## 4. Tema 1 — API (REST + JSON)

> Esta es la sección más importante del corte: casi todo el código del proyecto es la API.

### 4.1 API ≠ REST

- **API** es el **contrato**: operaciones, datos de entrada/salida y errores.
- **REST** es un **estilo arquitectónico** (Roy Fielding): recursos, HTTP, JSON, stateless, interfaz uniforme.
- El protocolo es **HTTP**; REST no es un protocolo ni una librería.

El enunciado pide “RESTful con JSON”: por eso las rutas usan **sustantivos** (`/juego`) y **métodos HTTP** (`POST`, `PUT`, `GET`), no `/crearJuego`.

### 4.2 Los seis endpoints del enunciado, uno por uno

| Enunciado | Implementación | Código de éxito | Errores principales |
| --- | --- | --- | --- |
| `POST /login` | `auth_routes.login` | 200 | 400 (username), 415 (Content-Type) |
| `POST /juego` | `game_routes.create_game` | **201 + Location** | 401, 400 (número), 415 |
| `PUT /juego/{ID}` | `game_routes.join_game` | 200 | 404, 400, 401, 415 |
| `POST /juego/{ID}/jugar` | `game_routes.play` | 200 | 404, **403 (turno)**, 400, 401 |
| `GET /juego/{ID}` | `game_routes.get_game` | 200 | 404, **403 (no participante)**, 401 |
| `GET /juego` | `game_routes.list_games` | 200 | 401 |

### 4.3 Métodos: seguro e idempotente

| Método | Seguro | Idempotente | En el proyecto |
| --- | --- | --- | --- |
| `GET` | Sí | Sí | consultar partida / listar |
| `POST` | No | No | `login`, crear partida, **jugar** (cada intento cambia el turno) |
| `PUT` | No | Sí (en teoría) | unirse — discutible, ver §4.7 |

**Trampa típica:** “POST siempre crea”. Aquí `POST /juego/{id}/jugar` **ejecuta una acción**, no crea un recurso persistente nuevo (aunque guarda el intento en `attempts`).

### 4.4 Códigos de estado con su línea exacta

| Código | Dónde se produce |
| --- | --- |
| `200` | `login`, `join_game`, `play`, `get_game`, `list_games`, `GET /` |
| `201` | `create_game` (con `Location`) |
| `400` | `ValueError` y `DomainError` → número inválido, body no objeto, username distinto, partida llena/terminada |
| `401` | `UnauthorizedError` → sin token, token inválido o expirado |
| `403` | `ForbiddenError` → no participa o no es su turno |
| `404` | `NotFoundError` → ID inexistente; `HTTPException` → ruta inexistente |
| `405` | `HTTPException` → método no admitido (ej. `DELETE /juego`) |
| `415` | `HTTPException` → `Content-Type` incorrecto |
| `500` | No controlado (por ejemplo, IDs agotados) — **mejora pendiente: handler JSON** |

**Regla de oro que conviene recitar:** “Si no sé quién eres → 401. Si sé quién eres pero no puedes → 403. Si mandaste mal los datos → 400. Si el recurso no existe → 404.”

### 4.5 Headers y JSON

```http
POST /juego HTTP/1.1
Authorization: Bearer eyJ1c2VybmFtZSI6ImFuYSJ9...
Content-Type: application/json

{"number":"4271"}
```

```http
HTTP/1.1 201 CREATED
Content-Type: application/json
Location: /juego/163590

{"id":"163590","creator":"ana","players":["ana"],"status":"waiting","turn":null,"attempts":[],"winner":null}
```

El número viaja como **string**. En Python, `jsonify` serializa y `request.get_json()` deserializa; en el front, `JSON.stringify`/`response.json()`.

### 4.6 Flujo de autenticación (stateless)

1. `POST /login {"username":"ana"}` → token firmado.
2. El front guarda el token en una variable JS.
3. Cada petición lleva `Authorization: Bearer <token>`.
4. `@require_auth` verifica firma + `max_age=3600` y pone `g.username`.
5. La ruta usa `g.username`; **nunca confía en el username del body** (lo compara en `PUT`).

### 4.7 Decisiones discutibles que conviene saber defender

| Decisión | Por qué se hizo | Alternativa |
| --- | --- | --- |
| `PUT` para unirse | El enunciado pide `PUT`; se interpreta como “actualizar la partida con el segundo jugador”. | `POST /juego/{id}/jugadores` sería más REST; `PUT` no es idempotente aquí. |
| `/jugar` como acción en la URL | Convención aceptada para operaciones no CRUD. | Modelar un recurso `intentos` con `POST /juego/{id}/intentos`. |
| Sin `PATCH` | No hay actualizaciones parciales. | — |
| `GET /juego` listo para todos los autenticados | Es un lobby; solo muestra información pública. | Filtrar por invitación. |
| Redirección en `GET /juego` y `GET /juego/{id}` sin token | Si el cliente es un navegador (`Accept: text/html`), `before_request` devuelve `302` a `/#/partidas` para que el front abra esa vista. | Para clientes API (`Accept: application/json` o con `Bearer`) se mantiene el `401`. |
| Errores `500` en HTML | No hay handler para excepciones no controladas. | Agregar `@app.errorhandler(Exception)` que devuelva JSON. |

### 4.8 CURL completo (copiar y pegar)

```bash
BASE=http://localhost:5000

TOKEN_ANA=$(curl -s -X POST $BASE/login -H 'Content-Type: application/json' \
  -d '{"username":"ana"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

TOKEN_LUIS=$(curl -s -X POST $BASE/login -H 'Content-Type: application/json' \
  -d '{"username":"luis"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

# Crear (201 + Location)
curl -i -X POST $BASE/juego -H "Authorization: Bearer $TOKEN_ANA" \
  -H 'Content-Type: application/json' -d '{"number":"4271"}'

# Unirse (usar el id devuelto)
curl -i -X PUT $BASE/juego/163590 -H "Authorization: Bearer $TOKEN_LUIS" \
  -H 'Content-Type: application/json' -d '{"username":"luis","number":"0123"}'

# Jugar
curl -i -X POST $BASE/juego/163590/jugar -H "Authorization: Bearer $TOKEN_ANA" \
  -H 'Content-Type: application/json' -d '{"number":"1234"}'

# Ver estado y listar
curl -i $BASE/juego/163590 -H "Authorization: Bearer $TOKEN_ANA"
curl -i $BASE/juego          -H "Authorization: Bearer $TOKEN_ANA"
```

---

## 5. Tema 2 — Docker

### 5.1 Lo que el proyecto hace **realmente**

**No hay `Dockerfile` en el repo.** En Kubernetes:

```yaml
initContainers:
  - name: download-code
    image: alpine/git:latest       # clona el repo en /source (emptyDir)
containers:
  - name: web
    image: python:3.12-slim        # imagen pública oficial
    args:
      - |
        pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0
        exec gunicorn --bind 0.0.0.0:5000 --workers 1 run:app
```

**Por qué se hizo así:** no hace falta publicar imagen propia; funciona en Killercoda con imágenes públicas; un `git push` + `rollout restart` actualiza el código.

**Contras que hay que saber admitir:** el arranque depende de GitHub y PyPI, es más lento, no es inmutable (toma el `HEAD`, no un commit fijo) y usa tags mutables (`latest`, `3.12-slim`).

### 5.2 Conceptos que caen en el corte

| Concepto | Definición | Ejemplo en el proyecto |
| --- | --- | --- |
| **Imagen** | Plantilla de solo lectura, construida por capas. | `python:3.12-slim`, `alpine/git:latest` |
| **Contenedor** | Instancia en ejecución de una imagen; comparte el kernel del host. | El contenedor `web` dentro del Pod. |
| **Registro** | Donde se publican imágenes. | Docker Hub (imágenes públicas). |
| **Capa** | Cada instrucción del Dockerfile; se cachea. | `pip install -r requirements.txt` |
| **`EXPOSE`** | Documenta el puerto, **no lo publica**. | Se publica con `-p 8080:5000` / Service. |
| **`0.0.0.0`** | Escucha en todas las interfaces; `127.0.0.1` solo dentro del contenedor. | `gunicorn --bind 0.0.0.0:5000` y `run.py`. |

**Contenedor vs VM:** el contenedor **comparte el kernel** del host (namespaces + cgroups); la VM incluye un SO completo e hipervisor.

### 5.3 Dockerfile propuesto para **este** código

Si el profesor dice “dockerice el proyecto”, esta es la respuesta, explicada línea a línea:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

COPY run.py .
COPY app ./app

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "run:app"]
```

| Instrucción | Por qué (conectado con el código) |
| --- | --- |
| `FROM python:3.12-slim` | Alineado con `requirements.txt` y con el despliegue. Mejor fijar versión/digest que `latest`. |
| `ENV PYTHONDONTWRITEBYTECODE=1` | No genera `__pycache__` (los hay en el repo local; en la imagen no deben estar). |
| `ENV PYTHONUNBUFFERED=1` | Logs en tiempo real. |
| `WORKDIR /app` | `run.py` importa `app`, así que ambos deben estar juntos. |
| `COPY requirements.txt .` antes que el código | Aprovecha la **caché**: si cambia `game.py`, no reinstala dependencias. |
| `RUN pip install ... gunicorn==23.0.0` | Instala Flask/itsdangerous y el servidor de producción. |
| `COPY run.py .` + `COPY app ./app` | Copia exactamente lo que `run.py` necesita. |
| `useradd` + `USER appuser` | No correr como root; si la app se compromete, el atacante no es root. |
| `EXPOSE 5000` | Documenta el puerto (el mismo de `run.py` y Gunicorn). |
| `CMD` en forma exec | Gunicorn recibe señales correctamente como PID 1. |
| `--workers 1` | **Clave:** los repositorios son diccionarios en memoria; 2 workers tendrían estados distintos. |

`.dockerignore` recomendado (el repo tiene `.gitignore`, pero Docker no lo usa):

```text
.git
.gitignore
.venv
__pycache__
*.pyc
docs
killercoda
README.md
Dockerfile
```

### 5.4 Comandos

```bash
docker build -t picas-y-fijas:1.0 .
docker run --rm -p 8080:5000 -e PICAS_SECRET_KEY=clave-segura picas-y-fijas:1.0
# http://localhost:8080

docker ps -a
docker logs -f <contenedor>
docker exec -it <contenedor> sh
```

`-p HOST:CONTENEDOR` → `-p 8080:5000` abre el 8080 del host y lo envía al 5000 del contenedor.

### 5.5 Errores típicos

| Síntoma | Causa | Solución |
| --- | --- | --- |
| Contenedor muere al arrancar | `CMD` incorrecto o excepción | `docker logs` |
| `localhost:8080` no responde | App escucha en `127.0.0.1` o falta `-p` | Escuchar en `0.0.0.0`, revisar `-p` |
| `COPY failed` | Archivo fuera del contexto o excluido | Revisar ruta y `.dockerignore` |
| `port is already allocated` | Puerto ocupado | Cambiar `-p` |
| Cambios no se ven | Caché de build | `docker build --no-cache` |

**Respuesta de examen:** “El contenedor corre Gunicorn en `0.0.0.0:5000`, con un worker porque el estado está en memoria. `EXPOSE` solo documenta; el puerto se publica con `-p` (local) o con un Service (Kubernetes).”

---

## 6. Tema 3 — RPC

### 6.1 Qué es RPC

**RPC** (*Remote Procedure Call*) permite llamar una función en otro proceso como si fuera local:

```python
resultado = juego_service.crear_juego("ana", "4271")
```

Por debajo hay red, serialización, timeouts y errores. Componentes: **stub** (cliente), **skeleton** (servidor), **IDL** (contrato, ej. `.proto`), **marshalling** y **transporte**.

### 6.2 REST vs RPC

| Aspecto | REST (lo que usa el proyecto) | RPC / gRPC |
| --- | --- | --- |
| Modelo | Recursos (`/juego/123`) | Acciones (`JuegoService.Jugar(...)`) |
| Interfaz | URL + método HTTP | IDL + stubs generados |
| Formato | JSON | protobuf (binario) |
| Acoplamiento | Débil | Fuerte (contrato) |
| Rendimiento | Bueno | Muy bueno (HTTP/2 + binario) |
| Streaming | Limitado | 4 modos |
| Navegador | Nativo | gRPC-Web / JSON-RPC |

**No hay uno mejor siempre.** REST brilla en APIs públicas y navegador; RPC en comunicación interna entre servicios, contratos estrictos y alto rendimiento.

### 6.3 ¿Por qué este proyecto usa REST y no RPC?

Respuesta lista para el corte:

> “El cliente principal es un **navegador** y el enunciado pide **REST con JSON**. `fetch` habla HTTP/JSON de forma nativa; gRPC requeriría gRPC-Web o un proxy, y no necesitamos streaming ni el rendimiento de protobuf para dos jugadores. Si el juego se dividiera en microservicios internos (matchmaking, motor de juego), ahí sí usaría gRPC.”

### 6.4 Cómo se vería el enunciado como RPC

Mapeo directo de los seis endpoints:

| REST (implementado) | RPC (hipotético) |
| --- | --- |
| `POST /login` | `AuthService.Login(LoginRequest)` |
| `POST /juego` | `JuegoService.CrearJuego(CrearJuegoRequest)` |
| `PUT /juego/{id}` | `JuegoService.Unirse(UnirseRequest)` |
| `POST /juego/{id}/jugar` | `JuegoService.Jugar(JugarRequest)` |
| `GET /juego/{id}` | `JuegoService.VerJuego(VerJuegoRequest)` |
| `GET /juego` | `JuegoService.ListarJuegos(ListarRequest)` |

### 6.5 JSON-RPC sobre el código existente (ejemplo concreto)

Se puede exponer un endpoint `/rpc` **reutilizando los servicios actuales** — el dominio no cambia:

```python
@app.post("/rpc")
def rpc():
    req = request.get_json() or {}
    rid = req.get("id")
    methods = {
        "crearJuego": lambda p: current_app.config["GAME_SERVICE"]
            .create_game(g.username, p["numero"]).to_dict(),
        "jugar": lambda p: current_app.config["GAME_SERVICE"]
            .play(p["id"], g.username, p["numero"]),
    }
    if req.get("jsonrpc") != "2.0" or req.get("method") not in methods:
        return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": rid}
    try:
        result = methods[req["method"]](req.get("params", {}))
        return {"jsonrpc": "2.0", "result": result, "id": rid}
    except Exception as e:
        return {"jsonrpc": "2.0", "error": {"code": -32602, "message": str(e)}, "id": rid}
```

Petición y respuesta:

```json
{"jsonrpc":"2.0","method":"crearJuego","params":{"numero":"4271"},"id":1}
{"jsonrpc":"2.0","result":{"id":"163590","status":"waiting"},"id":1}
```

**Punto importante:** la validación de 4 dígitos sigue ocurriendo en `Game._validate_number`; RPC solo cambia **cómo se llama**, no las reglas.

### 6.6 gRPC: contrato para el juego

```proto
syntax = "proto3";
package picas;

service JuegoService {
  rpc CrearJuego (CrearJuegoRequest) returns (JuegoReply);
  rpc Unirse     (UnirseRequest)     returns (JuegoReply);
  rpc Jugar      (JugarRequest)      returns (JugadaReply);
  rpc VerJuego   (VerJuegoRequest)   returns (JuegoReply);
  rpc ListarJuegos (ListarRequest)   returns (ListaReply);
}

message CrearJuegoRequest { string jugador = 1; string numero = 2; }
message JugarRequest      { string id = 1; string jugador = 2; string numero = 3; }
message JugadaReply       { string jugador = 1; string intento = 2; int32 fijas = 3; int32 picas = 4; }
message JuegoReply        { string id = 1; string creador = 2; repeated string jugadores = 3;
                            string estado = 4; string turno = 5; string ganador = 6; }
```

```bash
pip install grpcio grpcio-tools
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. picas.proto
```

**Stubs:** `JuegoServiceStub` en el cliente, `JuegoServiceServicer` en el servidor. Modos de streaming: unary, server-streaming, client-streaming y bidireccional.

**Códigos de error gRPC** (equivalentes a los HTTP del proyecto): `INVALID_ARGUMENT`≈400, `UNAUTHENTICATED`≈401, `PERMISSION_DENIED`≈403, `NOT_FOUND`≈404, `DEADLINE_EXCEEDED`=timeout, `UNAVAILABLE`=servidor caído.

**Buenas prácticas:** definir **deadlines** (`timeout=2`), reintentar solo operaciones **idempotentes**, usar backoff con jitter, **no reutilizar números de campo** en protobuf y usar TLS.

**Respuesta de examen:** “RPC es llamar funciones remotas como locales; REST modela recursos. En Picas y Fijas elegimos REST por el navegador y el contrato del enunciado. La capa de dominio está preparada para reutilizarse si se añade un adaptador gRPC.”

---

## 7. Tema 4 — Kubernetes

### 7.1 Los tres archivos YAML

#### `killercoda/namespace.yaml`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: picas-y-fijas
```

Aísla el Deployment, el Service y el Secret. **Los tres deben estar en el mismo namespace**; si el Deployment queda en `default`, el Service no encontrará sus Pods.

#### `killercoda/deployment.yaml` (línea por línea)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: picas-y-fijas
  namespace: picas-y-fijas
spec:
  replicas: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: picas-y-fijas
  template:
    metadata:
      labels:
        app: picas-y-fijas
    spec:
      volumes:
        - name: source
          emptyDir: {}
      initContainers:
        - name: download-code
          image: alpine/git:latest
          command: ["/bin/sh", "-ec"]
          args:
            - |
              git init /source/repo
              git -C /source/repo fetch --depth=1 https://github.com/jdjimenez1215/Picas-y-fijas.git HEAD
              git -C /source/repo reset --hard FETCH_HEAD
          volumeMounts:
            - name: source
              mountPath: /source
      containers:
        - name: web
          image: python:3.12-slim
          imagePullPolicy: IfNotPresent
          workingDir: /source/repo
          command: ["/bin/sh", "-ec"]
          args:
            - |
              pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0
              exec gunicorn --bind 0.0.0.0:5000 --workers 1 run:app
          volumeMounts:
            - name: source
              mountPath: /source
          resources:
            requests: { cpu: "250m", memory: "64Mi" }
            limits:   { cpu: "500m", memory: "128Mi" }
          ports:
            - name: http
              containerPort: 5000
          readinessProbe:
            httpGet:
              path: /
              port: http
```

| Campo | Para qué sirve |
| --- | --- |
| `replicas: 1` | El estado está en memoria (`MemoryGameRepository`); dos Pods tendrían partidas distintas. |
| `strategy: Recreate` | Mata el Pod viejo antes de crear el nuevo: evita dos versiones conviviendo con estados separados. |
| `selector.matchLabels` = `template.metadata.labels` | Si no coinciden, el Deployment no administra sus Pods. |
| `volumes: emptyDir` | Volumen temporal compartido entre `initContainer` y `web`; se borra con el Pod. |
| `initContainers.download-code` | Se ejecuta **antes** y debe terminar con éxito; clona el repo en `/source/repo`. |
| `imagePullPolicy: IfNotPresent` | No descarga la imagen si ya está en el nodo (útil en Killercoda). |
| `workingDir: /source/repo` | Ahí están `run.py`, `requirements.txt` y `app/`. |
| `pip install ...` en el arranque | Instala dependencias y Gunicorn; por eso **no hay Dockerfile**. |
| `exec gunicorn --bind 0.0.0.0:5000 --workers 1` | `0.0.0.0` para recibir tráfico del Service; **1 worker** por el estado en memoria. |
| `resources.requests` | Para que el scheduler elija nodo; `limits` para no exceder (si pasa memoria → `OOMKilled`). |
| `ports[].name: http` | Nombre referenciado por `targetPort: http` del Service y por la probe. `containerPort` es informativo. |
| Clave de firma | Ya no hay `env` ni Secret: `create_app` usa `os.urandom(32).hex()` si no hay `PICAS_SECRET_KEY`. Los tokens viven hasta que se reinicia el Pod. |
| `readinessProbe GET /` | Mientras falla, el Pod no recibe tráfico; no se reinicia (eso sería liveness). |

#### `killercoda/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: picas-y-fijas
  namespace: picas-y-fijas
spec:
  type: ClusterIP
  selector:
    app: picas-y-fijas
  ports:
    - port: 80
      protocol: TCP
      targetPort: http
```

- **ClusterIP**: accesible solo dentro del clúster (IP/DNS estable).
- `selector` coincide con los labels del Pod → el Service encuentra los endpoints.
- `port: 80` es donde escucha el Service; `targetPort: http` resuelve al **5000** del contenedor.
- Para acceder desde fuera se usa `kubectl port-forward ... 8080:80` (depuración). En producción: Ingress o LoadBalancer.

#### Sin Secret

El `deployment.yaml` ya **no** tiene `env` con `PICAS_SECRET_KEY`, así que **no hay que crear el Secret `picas-auth`**. `create_app` usa `os.urandom(32).hex()` y los tokens duran hasta que se reinicia el Pod.

### 7.2 Secuencia de despliegue

La guía actual (`killercoda/KILLERCODA.md` y `README.md`) recomienda pegar **un solo bloque** en la terminal `root@controlplane` (detén antes cualquier `port-forward` con `Ctrl+C`):

```bash
git clone https://github.com/jdjimenez1215/Picas-y-fijas.git
cd Picas-y-fijas
kubectl apply -f killercoda/namespace.yaml
kubectl apply -f killercoda/
kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=300s
kubectl -n picas-y-fijas port-forward --address 0.0.0.0 service/picas-y-fijas 8080:80
```

Cuando aparezca `Forwarding from 0.0.0.0:8080`, deja la terminal abierta y entra por **Traffic / Ports → 8080**. Si omites el primer `apply` del namespace, aparece `namespaces "picas-y-fijas" not found` porque los archivos se aplican en orden alfabético.

### 7.3 Diagnóstico (síntoma → causa → comando)

| Síntoma | Causa probable | Comando |
| --- | --- | --- |
| `namespaces "picas-y-fijas" not found` | Se aplicó la carpeta sin crear antes el namespace | `kubectl apply -f killercoda/namespace.yaml` y repetir |
| `error: unable to forward port because pod is not running` | El Pod está `Pending`; el túnel requiere `Running` | `get pods`, esperar al `rollout status` |
| `Init:Error` | Falló el clone de GitHub | `logs deployment/picas-y-fijas -c download-code` |
| `ImagePullBackOff` | Imagen/tag malo o registro caído | `describe pod`, `get events` |
| `CreateContainerConfigError` | Quedó un YAML antiguo que referencia el Secret | `git pull` y volver a aplicar |
| `CrashLoopBackOff` | Falló `pip install` o Gunicorn | `logs ... -c web` |
| `READY 0/1` | Readiness probe falla | `describe pod`, revisar `GET /` |
| Service sin respuesta | Selector o `targetPort` mal | `get endpoints`, `describe service` |
| `OOMKilled` | Límite de 128Mi bajo | Subir `limits.memory` |

Flujo: `get pods` → `describe pod` → `logs` → `get events` → `get endpoints`.

### 7.4 Limitaciones y mejoras

- Sin persistencia: reiniciar el Pod borra usuarios y partidas (`emptyDir` es temporal).
- No se puede escalar a varias réplicas sin BD/Redis compartido y una clave de firma común.
- `initContainer` clona el `HEAD`: `rollout undo` no garantiza volver al código anterior; haría falta fijar commit/tag o imagen versionada.
- Sin Ingress, TLS, HPA ni liveness probe.
- Las dependencias se instalan en cada arranque.

**Respuesta de examen:** “Uso 1 réplica, 1 worker y `Recreate` porque el estado vive en diccionarios en memoria. El `initContainer` prepara el código, el contenedor `web` corre Gunicorn en `0.0.0.0:5000`, y el Service `ClusterIP` en el puerto 80 redirige a `targetPort: http` (5000). Para escalar haría falta persistencia compartida.”

---

## 8. Flujo completo: una petición de punta a punta

Ejemplo: `POST /juego/163590/jugar` con `{"number":"1234"}`.

```text
1. index.html        → fetch con Content-Type + Authorization: Bearer
2. Flask             → enruta a game_routes.play
3. @require_auth     → verify_token(max_age=3600) → g.username
4. _json_object()    → request.get_json() valida que sea dict
5. GameService.play  → _get_or_raise(163590) (404 si no existe)
6. Game.evaluate     → pertenencia → estado → turno → formato
                     → fijas/picas → actualiza turno/ganador → attempts
7. GameService       → game_repo.save(game)
8. jsonify(result)   → 200 {"player","guess","fijas","picas"}
9. index.html        → GET /juego/{id} → repinta turno, historial y ganador
```

Los cuatro temas del corte aparecen aquí:

| Tema | Dónde aparece en el flujo |
| --- | --- |
| **API** | Pasos 1–4 y 8: endpoints, JSON, headers, códigos. |
| **Docker** | El proceso Flask/Gunicorn corre dentro de un contenedor `python:3.12-slim`. |
| **RPC** | No aparece: se eligió REST. El “llamado” `GameService.play` es **local**, no remoto; en RPC sería un stub. |
| **Kubernetes** | El contenedor vive en un Pod; el tráfico entra por el Service `ClusterIP:80 → http:5000`. |

---

## 9. Preguntas del corte respondidas desde el código

1. **¿Qué es una API?** Un contrato. En este repo: seis rutas documentadas en `README.md` e implementadas en `app/routes`.
2. **¿REST es un protocolo?** No, es un estilo; el protocolo es HTTP. Aquí se usa JSON y `Bearer`.
3. **¿401 o 403?** 401 = `UnauthorizedError` (token); 403 = `ForbiddenError` (turno/participante).
4. **¿Por qué el número es string?** Para conservar `"0123"` y validar longitud; `_validate_number` lo exige.
5. **¿Cómo se calculan picas y fijas?** `zip` para fijas; `sum(d in secret) - fijas` para picas.
6. **¿Cómo se decide quién empieza?** `choice(self.players)` al unirse el segundo jugador.
7. **¿Cómo se generan los IDs?** Seis dígitos distintos con `secrets`, sin cero inicial, verificando colisiones.
8. **¿Por qué `201` y `Location`?** Porque `POST /juego` crea un recurso; `url_for(".get_game", ...)` genera la URL.
9. **¿Por qué `GET /juego` no muestra intentos?** El filtro de claves del `list_games` deja solo `id, creator, players, status, winner`.
10. **¿Cómo se evita que vean el secreto?** `Game.to_dict()` no incluye `_secrets`.
11. **¿Imagen vs contenedor?** Imagen = plantilla; contenedor = instancia. Aquí `python:3.12-slim` es la imagen, `web` el contenedor.
12. **¿Qué hace `EXPOSE` / `containerPort`?** Documentan el puerto; no publican. Publica `-p` o el Service.
13. **¿Por qué `0.0.0.0`?** Para aceptar conexiones desde fuera del contenedor (Gunicorn y `run.py` lo hacen).
14. **¿Por qué un solo worker?** Porque `MemoryGameRepository` es un diccionario por proceso.
15. **¿Qué es un Pod / un Service?** Pod = unidad mínima (initContainer + web comparten volumen); Service = IP/DNS estable que selecciona Pods por labels.
16. **¿Por qué `replicas: 1` y `Recreate`?** Estado en memoria; dos Pods o dos versiones tendrían estados distintos.
17. **¿Qué pasa si falta el Secret?** `CreateContainerConfigError`.
18. **¿RPC vs REST?** RPC llama acciones con stubs/IDL; REST manipula recursos con HTTP. Aquí gana REST por el navegador y el enunciado.
19. **¿Cómo migraría a gRPC?** Reutilizando `GameService` y `AuthService` detrás de un `JuegoServiceServicer` con `picas.proto`.
20. **¿Cómo escalaría el proyecto?** BD/Redis para estado compartido, clave de firma común, varios workers y réplicas con Ingress.

---

## 10. Checklist final y límites

### Antes del corte, saber explicar sin mirar

- [ ] Los **6 endpoints** y sus códigos (`200/201/400/401/403/404/405/415`).
- [ ] La diferencia **401 vs 403** con ejemplos reales del juego.
- [ ] La **fórmula de picas y fijas** y el ejemplo `4271` vs `1234`.
- [ ] Los **3 estados** y cuándo se transiciona (`waiting → in_progress → finished`).
- [ ] La validación de **4 dígitos distintos** y por qué es string.
- [ ] Por qué `to_dict()` **no devuelve secretos**.
- [ ] Imagen vs contenedor, `EXPOSE` vs `-p`, `0.0.0.0`, usuario no root.
- [ ] REST vs RPC y **por qué este proyecto no usa RPC**.
- [ ] Pod, Deployment, Service, Secret, initContainer, `emptyDir`, probes, `port-forward`.
- [ ] Por qué **1 réplica y 1 worker** (estado en memoria).

### Límites honestos (para no quedar mal al preguntar)

- Sin base de datos: reiniciar borra partidas (lo permite el enunciado: “No es necesaria BD”).
- Sin Dockerfile: se instala todo en el arranque (se propone uno en §5.3).
- `PUT` para unirse no es plenamente idempotente (§4.7).
- Los errores `500` no se normalizan a JSON.
- Sin HTTPS, CORS, rate limiting ni revocación de tokens.
- Login por nombre, sin contraseña: adecuado para la demo, no para producción.

> **Frase de cierre:** “Cada decisión del código se puede defender desde el enunciado: seis endpoints REST con JSON, reglas puras en el dominio, estado en memoria para cumplir ‘sin BD’, y un despliegue en Kubernetes con una réplica porque el estado no se comparte entre procesos.”

---

> **Documentos relacionados:** `01_teoria_api_docker_rpc_kubernetes.md` (teoría), `02_apunte_parcial.md` (ejercicios), `03_sustentacion_proyecto.md` (guion de exposición), `README.md` (contrato y ejecución), `killercoda/KILLERCODA.md` (despliegue paso a paso).
