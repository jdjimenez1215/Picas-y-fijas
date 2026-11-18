# Sustentación del proyecto — Picas y Fijas

> **Versión defendida:** commit `e9f59b2` en la rama `main`.
> **Repositorio:** <https://github.com/jdjimenez1215/Picas-y-fijas>
> **Documentos de apoyo:** `01_teoria_api_docker_rpc_kubernetes.md` (teoría) y `02_apunte_parcial.md` (ejercicios y plantillas).
>
> Este documento está pensado para **hablar**, no para leer textualmente. Cada sección tiene la idea, el archivo que la respalda y una frase que puedes usar en la exposición.

---

## Índice

1. [Ficha rápida](#1-ficha-rápida)
2. [Discurso de 60 segundos](#2-discurso-de-60-segundos)
3. [Requisitos y cumplimiento](#3-requisitos-y-cumplimiento)
4. [Arquitectura](#4-arquitectura)
5. [Dominio y reglas del juego](#5-dominio-y-reglas-del-juego)
6. [Contrato de la API](#6-contrato-de-la-api)
7. [Autenticación y seguridad](#7-autenticación-y-seguridad)
8. [Persistencia y estado](#8-persistencia-y-estado)
9. [Frontend y experiencia de usuario](#9-frontend-y-experiencia-de-usuario)
10. [Docker: cómo se ejecuta y cómo se dockerizaría](#10-docker-cómo-se-ejecuta-y-cómo-se-dockerizaría)
11. [Kubernetes: despliegue paso a paso](#11-kubernetes-despliegue-paso-a-paso)
12. [Pruebas y evidencia](#12-pruebas-y-evidencia)
13. [Decisiones de diseño y trade-offs](#13-decisiones-de-diseño-y-trade-offs)
14. [Limitaciones y trabajo futuro](#14-limitaciones-y-trabajo-futuro)
15. [Guion de demostración](#15-guion-de-demostración)
16. [Preguntas probables del profesor](#16-preguntas-probables-del-profesor)
17. [Cierre de 30 segundos](#17-cierre-de-30-segundos)
18. [Referencia rápida](#18-referencia-rápida)

---

## 1. Ficha rápida

| Dato | Valor |
| --- | --- |
| **Nombre** | Picas y Fijas |
| **Tipo** | Juego de dos jugadores con interfaz web y API REST |
| **Lenguaje / framework** | Python 3.12 + Flask 3.1 |
| **Arquitectura** | Cliente-servidor en capas: rutas → servicios → dominio → repositorios |
| **Frontend** | HTML + CSS + JavaScript vanilla, una sola plantilla |
| **Persistencia** | En memoria del proceso (diccionarios) |
| **Autenticación** | Token firmado con `itsdangerous`, vigencia de 1 hora, header `Bearer` |
| **Despliegue** | Kubernetes (Killercoda): namespace, Secret, Deployment y Service |
| **Estado** | Funcional; commit `e9f59b2` |
| **Repositorio** | `https://github.com/jdjimenez1215/Picas-y-fijas` |
| **Entrada local** | `python -m run` → `http://localhost:5000` |
| **Entrada en Kubernetes** | `kubectl port-forward` → `http://localhost:8080` |

**Frase para abrir:** “Picas y Fijas es un juego de dos jugadores que implementé como una aplicación cliente-servidor con API REST en Flask, autenticación por token y despliegue en Kubernetes. El foco del proyecto fue separar bien las capas, cumplir un contrato HTTP claro y demostrar que la aplicación funciona igual en local y en un clúster.”

---

## 2. Discurso de 60 segundos

> “Picas y Fijas es un juego en el que cada jugador elige un número secreto de cuatro dígitos distintos. Por turnos, cada uno intenta adivinar el número del rival. Por cada dígito acertado en la posición correcta se cuenta una **fija**; por cada dígito que existe pero está en otra posición se cuenta una **pica**. Gana quien consigue cuatro fijas.
>
> La aplicación tiene un frontend web en HTML y JavaScript, una API REST en Flask y un modelo de dominio que concentra las reglas. La arquitectura está separada en rutas, servicios, dominio y repositorios: las rutas solo hablan HTTP, los servicios coordinan casos de uso, el dominio valida las reglas y los repositorios encapsulan el almacenamiento. La autenticación usa tokens firmados con vigencia de una hora; las partidas se guardan en memoria y el lobby se actualiza automáticamente cada dos segundos.
>
> El despliegue está en Kubernetes: un namespace, un Secret para la clave de firma, un Deployment con un `initContainer` que descarga el código y un Service `ClusterIP`. Usé una réplica y un worker porque el estado vive en memoria; esa es una decisión consciente y una de las principales líneas de mejora, junto con persistencia real, pruebas automatizadas y una imagen Docker propia.”

**Si solo tienes 30 segundos:** di la primera frase, menciona “REST + Flask + Kubernetes”, y cierra con “la limitación principal es que el estado es en memoria, y la siguiente mejora es persistirlo”.

---

## 3. Requisitos y cumplimiento

| Requisito | Cómo se cumple | Evidencia |
| --- | --- | --- |
| Juego para dos jugadores | `Game.join` solo acepta un segundo jugador y cambia a `in_progress`. | `app/domain/game.py` |
| Cada jugador elige cuatro dígitos distintos | `_validate_number` exige string, 4 caracteres ASCII, dígitos y `len(set(number)) == 4`. | `app/domain/game.py` |
| Sortear el primer turno | `random.choice(self.players)` al unirse el segundo jugador. | `Game.join` |
| Calcular picas y fijas | `evaluate` compara posición y pertenencia contra el secreto del rival. | `Game.evaluate` |
| Ganar con cuatro fijas | Si `fijas == 4`, estado `finished`, `winner` y turno `None`. | `Game.evaluate` |
| Crear partida | `POST /juego` con número secreto; responde `201` y `Location`. | `app/routes/game_routes.py` |
| Unirse a partida | `PUT /juego/{id}` con `username` y número; valida que el usuario coincida con el token. | `game_routes.py` |
| Jugar un intento | `POST /juego/{id}/jugar`; valida participante, estado y turno. | `game_routes.py` |
| Consultar partida | `GET /juego/{id}`; solo participantes. | `game_routes.py` |
| Listar partidas | `GET /juego`; resumen para el lobby. | `game_routes.py` |
| API REST + JSON | Rutas con sustantivos, métodos HTTP, cuerpos JSON y errores JSON. | `README.md`, rutas |
| Autenticación | `POST /login` devuelve token firmado; rutas protegidas con `Bearer`. | `auth_service.py`, `decorators.py` |
| Identificadores únicos | Seis dígitos distintos, sin cero inicial, verificación de colisión. | `game_service.py` |
| Lobby con disponibles y terminadas | El front separa `status !== "finished"` y `status === "finished"`. | `index.html` |
| Actualización automática | Polling cada 2 segundos en lobby y partida. | `index.html` |
| Repositorio público | Código publicado en GitHub. | URL del repositorio |
| Despliegue en Kubernetes | Namespace, Secret, Deployment y Service en `killercoda/`. | `killercoda/*.yaml` |
| Interfaz web | Una sola página con login, lobby, partida y resultados. | `app/templates/index.html` |
| Manejo de errores | `400`, `401`, `403`, `404`, `405`, `415` en JSON. | `app/__init__.py` |
| Documentación | README con ejecución local, API y límites. | `README.md` |

### 3.1 Mapa de los cuatro temas del parcial

| Tema | Dónde está en el proyecto | Qué puedo defender |
| --- | --- | --- |
| **API** | `app/routes/*.py`, `README.md` | REST + JSON, métodos, códigos, headers, validación, errores, cURL. |
| **Docker** | `killercoda/deployment.yaml` (contenedor `python:3.12-slim`) | Imagen vs contenedor, Dockerfile propuesto, `EXPOSE`, `-p`, `0.0.0.0`, usuario no root. |
| **RPC** | No se usa; el proyecto es REST. | Qué es RPC, REST vs RPC, JSON-RPC, gRPC/protobuf, cómo migrarían los endpoints. |
| **Kubernetes** | `killercoda/namespace.yaml`, `deployment.yaml`, `service.yaml` | Pod, Deployment, Service, Secret, initContainer, probes, `port-forward`, diagnóstico. |

**Matiz importante:** el proyecto **se ejecuta en contenedores** dentro de Kubernetes, pero **no construye una imagen propia**. Usa `python:3.12-slim` y descarga el código con un `initContainer`. Si el profesor exige un Dockerfile, en la sección 10 está la propuesta y la justificación.

**Frase para esta sección:** “Cada requisito tiene un archivo responsable. La regla del juego no está en la ruta ni en el HTML: está en el dominio, y eso permite probarla y cambiarla sin tocar HTTP.”

---

## 4. Arquitectura

### 4.1 Diagrama de capas

```text
┌──────────────────────────────────────────────┐
│ Navegador: HTML + CSS + JavaScript vanilla   │
│  - login, lobby, partida, polling cada 2 s   │
└──────────────────────┬───────────────────────┘
                       │ fetch JSON + Bearer token
                       ▼
┌──────────────────────────────────────────────┐
│ Flask: app factory (`create_app`)            │
│  - registra blueprints y manejadores de error│
│  - inyecta repositorios y servicios          │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ Rutas (`app/routes`)                         │
│  - leen HTTP, validan JSON, exigen token     │
│  - no contienen reglas del juego             │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ Servicios (`app/services`)                   │
│  - casos de uso: crear, unir, jugar, listar  │
│  - generan IDs y coordinan repositorios      │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ Dominio (`app/domain`)                       │
│  - Game, User, estados y excepciones         │
│  - reglas: 4 dígitos, turno, picas/fijas     │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ Repositorios (`app/repositories`)            │
│  - interfaces: GameRepository, UserRepository│
│  - implementación en memoria (dict)          │
└──────────────────────────────────────────────┘
```

### 4.2 Archivos y responsabilidades

| Archivo | Responsabilidad | Lo que **no** debería hacer |
| --- | --- | --- |
| `run.py` | Crear la app y arrancar el servidor local. | Contener reglas del juego. |
| `app/__init__.py` | **Composition root**: crear Flask, repositorios, servicios, registrar blueprints y errores. | Implementar endpoints. |
| `app/routes/auth_routes.py` | `POST /login`. | Validar la firma del token (eso lo hace el servicio). |
| `app/routes/game_routes.py` | Endpoints `/juego`, lectura de JSON y respuestas HTTP. | Calcular picas/fijas. |
| `app/routes/decorators.py` | Extraer y verificar `Authorization: Bearer`. | Decidir si es el turno. |
| `app/services/auth_service.py` | Registro automático, firma y verificación de tokens. | Guardar partidas. |
| `app/services/game_service.py` | Crear, unir, jugar, consultar y listar; generar IDs. | Validar dígitos (eso es dominio). |
| `app/domain/game.py` | Reglas e invariantes del juego. | Saber qué es HTTP. |
| `app/domain/user.py` | Modelo de usuario. | Autenticar. |
| `app/domain/exceptions.py` | Errores de negocio (`NotFoundError`, `UnauthorizedError`, `ForbiddenError`). | Traducir a HTTP (eso lo hace `app/__init__.py`). |
| `app/repositories/*.py` | Contratos e implementación en memoria. | Reglas del juego. |
| `app/templates/index.html` | Interfaz, fetch, polling y navegación. | Reglas del juego. |
| `killercoda/*.yaml` | Despliegue en Kubernetes. | Lógica de la app. |
| `requirements.txt` | Dependencias fijadas. | Configuración de producción. |
| `README.md` | Contrato, ejecución y límites. | Código. |

### 4.3 Flujo completo de una petición

Ejemplo: `POST /juego/482913/jugar` con `{"number":"1234"}`.

1. El navegador arma `fetch` con `Content-Type: application/json` y `Authorization: Bearer TOKEN`.
2. Flask enruta a `play` en `game_routes.py`.
3. `@require_auth` lee el header, verifica la firma con `AuthService.verify_token` y guarda `g.username`.
4. La ruta lee el JSON con `_json_object()` y llama a `GameService.play`.
5. `GameService` busca la partida en `MemoryGameRepository`; si no existe, lanza `NotFoundError`.
6. `Game.evaluate` verifica que el jugador pertenezca, que sea su turno, valida el número, calcula picas/fijas y actualiza estado/turno/ganador.
7. El servicio guarda la partida actualizada y devuelve el resultado.
8. La ruta responde `jsonify(result)` con `200`.
9. El front recibe el resultado, vuelve a consultar `GET /juego/{id}` y actualiza turno, intentos y mensaje.

**Frase:** “La ruta no sabe jugar; solo traduce HTTP. El servicio no sabe de picas; solo coordina. El dominio no sabe de Flask; solo cumple las reglas. Esa separación es lo que hace el proyecto defendible.”

### 4.4 Inyección de dependencias y inversión de dependencias

`GameService` recibe un `GameRepository`, no un `MemoryGameRepository`:

```python
class GameService:
    def __init__(self, game_repo: GameRepository):
        self.game_repo = game_repo
```

`AuthService` recibe un `UserRepository`:

```python
class AuthService:
    def __init__(self, user_repo: UserRepository, secret_key: str, token_max_age: int = 3600):
        ...
```

En `create_app` se decide la implementación concreta:

```python
user_repo = MemoryUserRepository()
game_repo = MemoryGameRepository()
auth_service = AuthService(user_repo, secret_key=secret_key)
game_service = GameService(game_repo)
```

**Por qué importa:** para pasar a PostgreSQL solo se crea `PostgresGameRepository` y se inyecta; el dominio y los servicios no cambian. Eso es **inversión de dependencias** y **repository pattern**.

### 4.5 App factory y blueprints

- **App factory** (`create_app`): permite crear varias apps con configuración distinta, por ejemplo una con clave de prueba para tests y otra con la clave real. Evita una app global difícil de testear.
- **Blueprint**: agrupa rutas por dominio (`auth_bp`, `game_bp`) y permite registrar prefijos (`url_prefix="/juego"`).
- **Composition root**: `create_app` es el único lugar donde se conectan repositorios, servicios, rutas y manejadores. Si algo falta, se ve ahí.

**Pregunta probable:** “¿Por qué no puso todo en un solo archivo?” Porque el proyecto crece y se vuelve difícil de probar; separar permite cambiar almacenamiento, probar dominio sin Flask y leer el código por responsabilidades.

---

## 5. Dominio y reglas del juego

### 5.1 Estados

```python
class GameStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
```

| Estado | Significado | Quién puede actuar |
| --- | --- | --- |
| `waiting` | Solo está el creador; falta el segundo jugador. | El creador puede ver; otro usuario puede unirse. |
| `in_progress` | Hay dos jugadores y un turno. | Solo el jugador del turno puede jugar. |
| `finished` | Alguien acertó cuatro fijas. | Nadie juega; los participantes pueden consultar. |

### 5.2 Crear una partida

```python
game = Game(id=..., secret=secret, creator=creator)
```

El constructor:

- valida el número secreto;
- guarda `id`, `creator`;
- inicializa `players = [creator]`;
- guarda el secreto en `_secrets[creator]`;
- inicializa `attempts = []`;
- estado `waiting`, turno `None`, ganador `None`.

**Invariante:** el número secreto nunca se expone en `to_dict()`. Solo se guarda en `_secrets`, que es privado por convención.

### 5.3 Unirse

```python
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
```

Orden de validaciones:

1. No unirse a una partida terminada.
2. No unirse dos veces con el mismo nombre.
3. No unirse si ya hay dos jugadores.
4. Validar el número.
5. Agregar jugador y secreto.
6. Sortear turno.
7. Cambiar a `in_progress`.

**Pregunta probable:** “¿Qué pasa si el creador intenta unirse a su propia partida?” Recibe `400` con “ya está en la partida”, porque `player in self.players` se cumple.

### 5.4 Jugar y calcular picas/fijas

```python
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
```

**Fórmula:**

- **Fija:** mismo dígito en la misma posición.
- **Pica:** dígito que existe en el secreto pero no en esa posición.
- `picas = dígitos del intento que pertenecen al secreto − fijas`.

**Ejemplo con secreto `4271` e intento `4172`:**

| Posición | Intento | Secreto | Resultado |
| --- | --- | --- | --- |
| 0 | 4 | 4 | Fija |
| 1 | 1 | 2 | Pica (1 está en el secreto) |
| 2 | 7 | 7 | Fija |
| 3 | 2 | 1 | Pica (2 está en el secreto) |

Total: **2 fijas, 2 picas**.

**Por qué no se cuenta dos veces un dígito:** la validación exige dígitos distintos, así que cada dígito aparece una sola vez en el intento y en el secreto.

**Orden de validaciones:** pertenencia → estado → turno → formato. Si un jugador ajeno intenta jugar, recibe `403` aunque el número sea inválido; primero se controla el permiso, no el dato.

### 5.5 Validación del número

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
| `"4271"` | Válido |
| `"0123"` | Válido (conserva el cero inicial) |
| `"1123"` | Inválido (dígitos repetidos) |
| `"123"` | Inválido (longitud) |
| `"12345"` | Inválido (longitud) |
| `"12a4"` | Inválido (no dígito) |
| `1234` (número) | Inválido (no es string) |
| `"１２３４"` (Unicode) | Inválido (`isascii`) |
| `" 123"` | Inválido (espacio) |

**Por qué string:** `"0123"` como número sería `123` y perdería el cero inicial. Además, la longitud y los dígitos se validan exactamente.

### 5.6 Generación del identificador

```python
def _new_game_id(self) -> str:
    used = {game.id for game in self.game_repo.find_all()}
    if len(used) >= 136_080:
        raise RuntimeError("No quedan identificadores de partida disponibles")
    while True:
        game_id = self._candidate_game_id()
        if game_id not in used:
            return game_id

@staticmethod
def _candidate_game_id() -> str:
    first = secrets.choice("123456789")
    pool = [digit for digit in "0123456789" if digit != first]
    rest = [pool.pop(secrets.randbelow(len(pool))) for _ in range(5)]
    return first + "".join(rest)
```

- **Seis dígitos distintos.**
- **Sin cero inicial:** el primer dígito sale de `1..9`.
- **Combinaciones:** `9 × 9 × 8 × 7 × 6 × 5 = 136.080`.
- **Aleatorio criptográfico:** `secrets`, no `random`, para reducir predicibilidad.
- **Colisión:** si el candidato ya existe, se repite el ciclo.
- **Agotamiento:** si ya se usaron los 136.080, lanza `RuntimeError` (en la API sería un `500`).
- **Costo:** `find_all()` recorre todas las partidas; con pocas partidas es despreciable.

**Preguntas probables:**

- “¿Por qué no un UUID?” Porque el ID se muestra y se comparte en la interfaz; seis dígitos son legibles. Un UUID sería más seguro contra enumeración, pero menos amigable.
- “¿Por qué no un consecutivo?” Porque revela cuántas partidas hay y es trivial de adivinar. El aleatorio dificulta la enumeración.
- “¿Es seguro?” No es un mecanismo de seguridad: la autorización real está en el token y en la validación de participantes. El ID solo identifica.

### 5.7 Privacidad de los secretos

`Game.to_dict()` devuelve:

```python
{
    "id": self.id,
    "creator": self.creator,
    "players": list(self.players),
    "status": self.status.value,
    "turn": self.turn,
    "attempts": list(self.attempts),
    "winner": self.winner,
}
```

**No devuelve `_secrets`.** Por eso `GET /juego/{id}` muestra intentos, turno y ganador, pero nunca el número que el rival eligió. La lista `GET /juego` es aún más reducida: solo `id`, `creator`, `players`, `status` y `winner`.

**Frase:** “El secreto nunca sale del servidor. El cliente conoce sus propios intentos y los del rival, pero no los números secretos.”

---

## 6. Contrato de la API

### 6.1 Resumen de endpoints

| Método | Ruta | Autenticación | Cuerpo | Respuesta exitosa |
| --- | --- | --- | --- | --- |
| `GET` | `/` | No | — | `200` HTML |
| `POST` | `/login` | No | `{"username":"ana"}` | `200` `{"token":"..."}` |
| `POST` | `/juego` | Bearer | `{"number":"4271"}` | `201` partida + `Location` |
| `PUT` | `/juego/{id}` | Bearer | `{"username":"luis","number":"0123"}` | `200` partida con dos jugadores |
| `POST` | `/juego/{id}/jugar` | Bearer | `{"number":"1234"}` | `200` resultado de la jugada |
| `GET` | `/juego/{id}` | Bearer | — | `200` estado completo para participantes |
| `GET` | `/juego` | Bearer | — | `200` resumen de partidas |

**Convenciones:**

- Todos los cuerpos son JSON y requieren `Content-Type: application/json`.
- Las rutas de `/juego` requieren `Authorization: Bearer <token>`.
- El `number` siempre es **string** de cuatro dígitos distintos.
- Los errores tienen forma `{"error": "..."}` o `{"error": "...", "description": "..."}`.

### 6.2 `POST /login`

**Propósito:** identificar al jugador y devolver un token firmado. Si el usuario no existe, se registra automáticamente.

**Petición:**

```http
POST /login HTTP/1.1
Content-Type: application/json

{"username":"ana"}
```

**Respuesta `200`:**

```json
{"token":"eyJ1c2VybmFtZSI6ImFuYSJ9.avzKOA.m7pcs_P8VnVXewGuj2yv5eu_JE0"}
```

**Errores:**

| Caso | Código | Cuerpo |
| --- | --- | --- |
| Falta `username` o no es string | `400` | `{"error":"username es obligatorio"}` |
| `Content-Type` incorrecto | `415` | `{"error":"Unsupported Media Type", ...}` |
| JSON mal formado | `400` | Error de Flask en JSON |

**Nota:** no hay contraseña. Es una **identificación por nombre** para el alcance académico; cualquiera puede entrar con cualquier nombre. El token evita que se modifique el nombre en el camino, pero no prueba identidad real.

### 6.3 `POST /juego`

**Propósito:** crear una partida con el número secreto del creador.

**Petición:**

```http
POST /juego HTTP/1.1
Authorization: Bearer TOKEN_ANA
Content-Type: application/json

{"number":"4271"}
```

**Respuesta `201`:**

```http
HTTP/1.1 201 CREATED
Content-Type: application/json
Location: /juego/163590
```

```json
{
  "attempts": [],
  "creator": "ana",
  "id": "163590",
  "players": ["ana"],
  "status": "waiting",
  "turn": null,
  "winner": null
}
```

**Errores:**

| Caso | Código | Cuerpo |
| --- | --- | --- |
| Sin token | `401` | `{"error":"Falta el header Authorization: Bearer <token>"}` |
| Token inválido/vencido | `401` | `{"error":"Token inválido"}` / `{"error":"Token expirado"}` |
| `number` ausente, no string, longitud distinta o repetido | `400` | `{"error":"El número ..."}` |
| Body no es objeto JSON | `400` | `{"error":"El cuerpo debe ser un objeto JSON"}` |
| `Content-Type` incorrecto | `415` | JSON de error |

**Detalle:** el `Location` se genera con `url_for(".get_game", game_id=game.id)`, no se escribe a mano.

### 6.4 `PUT /juego/{id}`

**Propósito:** unirse a una partida `waiting` con el número secreto del segundo jugador.

**Petición:**

```http
PUT /juego/163590 HTTP/1.1
Authorization: Bearer TOKEN_LUIS
Content-Type: application/json

{"username":"luis","number":"0123"}
```

**Respuesta `200`:**

```json
{
  "attempts": [],
  "creator": "ana",
  "id": "163590",
  "players": ["ana", "luis"],
  "status": "in_progress",
  "turn": "luis",
  "winner": null
}
```

**Errores:**

| Caso | Código | Cuerpo |
| --- | --- | --- |
| Partida inexistente | `404` | `{"error":"No existe una partida con id '...'"}` |
| `username` no coincide con el token | `400` | `{"error":"username debe coincidir con el usuario del token"}` |
| Partida terminada | `400` | `{"error":"No puedes unirte: la partida ya terminó"}` |
| Ya hay dos jugadores | `400` | `{"error":"La partida ya tiene dos jugadores"}` |
| El jugador ya está | `400` | `{"error":"El jugador '...' ya está en la partida"}` |
| Número inválido | `400` | `{"error":"..."}` |

**Discusión de diseño:** usar `PUT` para “unirse” es discutible. `PUT` sugiere reemplazar un recurso y ser idempotente; aquí una segunda llamada falla porque el jugador ya está. Una alternativa más REST sería `POST /juego/{id}/jugadores`. Se mantuvo `PUT` por el contrato trabajado en clase y porque la operación “actualiza la partida con el segundo jugador”. Es una de las deudas de diseño que se pueden mencionar.

### 6.5 `POST /juego/{id}/jugar`

**Propósito:** registrar un intento del jugador del turno.

**Petición:**

```http
POST /juego/163590/jugar HTTP/1.1
Authorization: Bearer TOKEN_ANA
Content-Type: application/json

{"number":"1234"}
```

**Respuesta `200`:**

```json
{"player":"ana","guess":"1234","fijas":0,"picas":3}
```

**Errores:**

| Caso | Código | Cuerpo |
| --- | --- | --- |
| Partida inexistente | `404` | `{"error":"No existe una partida con id '...'"}` |
| No participa | `403` | `{"error":"No perteneces a esta partida"}` |
| Partida no está en juego | `400` | `{"error":"La partida no está en juego"}` |
| No es su turno | `403` | `{"error":"No es tu turno"}` |
| Número inválido | `400` | `{"error":"..."}` |

**Importante:** la respuesta de jugar **no** incluye el estado completo; solo el resultado. El front hace luego `GET /juego/{id}` para actualizar turno, intentos y ganador. Esto mantiene la acción pequeña y evita duplicar la representación.

### 6.6 `GET /juego/{id}`

**Propósito:** consultar el estado completo de una partida. Solo participantes.

**Petición:**

```http
GET /juego/163590 HTTP/1.1
Authorization: Bearer TOKEN_ANA
```

**Respuesta `200`:**

```json
{
  "attempts": [
    {"player":"ana","guess":"1234","fijas":0,"picas":3}
  ],
  "creator": "ana",
  "id": "163590",
  "players": ["ana","luis"],
  "status": "in_progress",
  "turn": "luis",
  "winner": null
}
```

**Errores:**

| Caso | Código | Cuerpo |
| --- | --- | --- |
| No existe | `404` | `{"error":"No existe una partida con id '...'"}` |
| El usuario no es participante | `403` | `{"error":"Solo los participantes pueden consultar esta partida"}` |
| Sin token | `401` | `{"error":"Falta el header Authorization: Bearer <token>"}` |

**Por qué restringir:** los intentos y el estado detallado son información de la partida; el lobby no necesita verlos. La lista pública se limita a un resumen.

### 6.7 `GET /juego`

**Propósito:** alimentar el lobby con todas las partidas.

**Respuesta `200`:**

```json
[
  {
    "creator": "ana",
    "id": "163590",
    "players": ["ana","luis"],
    "status": "in_progress",
    "winner": null
  },
  {
    "creator": "luis",
    "id": "209867",
    "players": ["luis","ana"],
    "status": "finished",
    "winner": "ana"
  }
]
```

**Detalle:** la ruta filtra las claves:

```python
{key: value for key, value in game.to_dict().items()
 if key in {"id", "creator", "players", "status", "winner"}}
```

No incluye `attempts` ni `turn` para que el lobby sea liviano. El front filtra `status !== "finished"` para **Disponibles** y `status === "finished"` para **Terminadas**.

**Posible pregunta:** “¿No es un problema que cualquier autenticado vea todas las partidas?” Es el comportamiento esperado de un lobby. Solo se muestra información pública de la partida; los detalles y secretos siguen protegidos. Si se quisiera privacidad, se filtraría por invitación.

### 6.8 Mapa de errores

| Excepción / caso | HTTP | Manejo |
| --- | --- | --- |
| `NotFoundError` | `404` | `handle_not_found` |
| `UnauthorizedError` | `401` | `handle_unauthorized` |
| `ForbiddenError` | `403` | `handle_forbidden` |
| `DomainError` | `400` | `handle_domain` |
| `ValueError` | `400` | `handle_value` |
| `HTTPException` (404 ruta, 405, 415…) | El de la excepción | `handle_http_exception` |
| `RuntimeError` (IDs agotados) | `500` | Sin handler específico; Flask responde HTML |
| Excepción no controlada | `500` | **No hay handler JSON específico**; Flask responde HTML |

**Frase:** “Los errores de negocio y los HTTP comunes están normalizados a JSON. Un `500` no controlado conserva el formato de Flask; sería una mejora agregar un handler que también devuelva JSON y registre un ID de correlación.”

### 6.9 Probar el contrato con cURL

```bash
BASE=http://localhost:5000

# 1. Login
TOKEN_ANA=$(curl -s -X POST $BASE/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"ana"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

# 2. Crear
curl -i -X POST $BASE/juego \
  -H "Authorization: Bearer $TOKEN_ANA" \
  -H 'Content-Type: application/json' \
  -d '{"number":"4271"}'

# 3. Error de validación
curl -i -X POST $BASE/juego \
  -H "Authorization: Bearer $TOKEN_ANA" \
  -H 'Content-Type: application/json' \
  -d '{"number":"1123"}'

# 4. Sin token
curl -i -X POST $BASE/juego \
  -H 'Content-Type: application/json' \
  -d '{"number":"4271"}'

# 5. Método incorrecto
curl -i -X DELETE $BASE/juego \
  -H "Authorization: Bearer $TOKEN_ANA"
```

---

## 7. Autenticación y seguridad

### 7.1 Flujo

```text
POST /login {"username":"ana"}
        │
        ▼
AuthService.login
  - valida username
  - si no existe, lo registra
  - serializer.dumps({"username": "ana"})
        │
        ▼
{"token": "..."}  ← token firmado, no cifrado
        │
        ▼
Front guarda token en una variable JS
        │
        ▼
Cada request: Authorization: Bearer <token>
        │
        ▼
@require_auth
  - exige "Bearer "
  - AuthService.verify_token
  - loads(max_age=3600)
  - g.username = username
        │
        ▼
La ruta usa g.username
```

### 7.2 Cómo se firma

```python
serializer = URLSafeTimedSerializer(secret_key, salt="picas-y-fijas-auth")
token = serializer.dumps({"username": username})
data = serializer.loads(token, max_age=3600)
```

| Aspecto | Detalle |
| --- | --- |
| Librería | `itsdangerous` |
| Algoritmo | Firma HMAC con la clave secreta |
| Vigencia | `max_age=3600` segundos (1 hora) |
| Contenido | `{"username": "..."}` visible (no está cifrado) |
| Manipulación | Si alguien cambia el username, la firma falla |
| Clave | `PICAS_SECRET_KEY` o una aleatoria al arrancar |
| Expiración | `SignatureExpired` → `401` |
| Firma inválida | `BadSignature` → `401` |

**Importante:** el token está **firmado, no cifrado**. Cualquiera puede decodificar el username, pero no modificarlo sin la clave. No se debe poner información sensible dentro.

### 7.3 `require_auth`

```python
def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise UnauthorizedError("Falta el header Authorization: Bearer <token>")
        token = auth_header[len("Bearer "):]
        auth_service = current_app.config["AUTH_SERVICE"]
        username = auth_service.verify_token(token)
        g.username = username
        return f(*args, **kwargs)
    return wrapper
```

- Exige el prefijo exacto `Bearer `.
- Si falta, `401`.
- Si el token es inválido o vencido, `AuthService` lanza `UnauthorizedError` → `401`.
- Guarda el username en `g`, que vive solo durante la petición.
- **Stateless:** el servidor no guarda sesiones; verifica la firma en cada request.

### 7.4 `401` vs `403` en el proyecto

| Situación | Código | Explicación |
| --- | --- | --- |
| No hay header `Authorization` | `401` | No sé quién eres. |
| Token mal firmado | `401` | La credencial no es válida. |
| Token vencido | `401` | La credencial ya no sirve; vuelve a autenticarte. |
| Token válido, pero no participas en la partida | `403` | Sé quién eres, pero no tienes permiso. |
| Token válido, pero no es tu turno | `403` | Sé quién eres, pero no puedes jugar ahora. |

### 7.5 Decisiones de seguridad y límites

| Tema | Decisión | Consecuencia |
| --- | --- | --- |
| Login sin contraseña | Identificación por nombre | Cualquiera puede entrar con cualquier nombre; no es autenticación fuerte. |
| Token firmado | `itsdangerous` | Simple, sin estado, suficiente para el alcance. |
| Vigencia 1 hora | `max_age=3600` | Hay que volver a iniciar sesión; no hay refresh token. |
| Logout | Borra el token en JS | El token copiado sigue válido hasta vencer; no hay revocación. |
| Almacenamiento del token | Variable JS, no `localStorage` | Recargar la página cierra la sesión; reduce persistencia ante XSS. |
| HTTPS | No configurado | En producción es obligatorio; el token viaja en el header. |
| CORS | No configurado | El front es del mismo origen; si se separa, hay que configurarlo. |
| CSRF | No aplica | Se usa header `Bearer`, no cookies de sesión. |
| Rate limiting | No implementado | Se podría abusar de `/login` o probar IDs. |
| Secretos en respuestas | Nunca se devuelven | `to_dict` excluye `_secrets`. |
| XSS | `textContent`, no `innerHTML` | Los datos del servidor se insertan como texto. |

**Frase:** “La autenticación es adecuada para un ejercicio académico, pero no para producción: falta contraseña, HTTPS, revocación y rate limiting. Lo importante es que el token está firmado y que el servidor nunca confía en el username que manda el cliente: lo saca del token.”

### 7.6 Qué pasaría si…

| Escenario | Efecto |
| --- | --- |
| Se cambia `PICAS_SECRET_KEY` | Todos los tokens existentes dejan de ser válidos; los usuarios deben volver a entrar. |
| Se reinicia el servidor sin `PICAS_SECRET_KEY` | Se genera una clave nueva; los tokens viejos se invalidan. Además se pierden partidas. |
| Hay dos workers con claves distintas | Un token firmado por uno puede ser rechazado por el otro. En K8s se usa un Secret compartido. |
| Alguien copia el token | Puede usarlo hasta que venza; no hay revocación. |
| Alguien intenta cambiar el username del token | La firma falla y recibe `401`. |
| Alguien mira el token | Puede leer el username (no está cifrado), pero no modificarlo. |

---

## 8. Persistencia y estado

### 8.1 El patrón repositorio

Los contratos están en `app/repositories/`:

```python
class GameRepository(ABC):
    @abstractmethod
    def save(self, game: Game) -> None: ...

    @abstractmethod
    def find_by_id(self, game_id: str) -> Optional[Game]: ...

    @abstractmethod
    def find_all(self) -> List[Game]: ...
```

```python
class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> None: ...

    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]: ...
```

Las implementaciones concretas son diccionarios:

```python
class MemoryGameRepository(GameRepository):
    def __init__(self):
        self._games: dict[str, Game] = {}

    def save(self, game: Game) -> None:
        self._games[game.id] = game

    def find_by_id(self, game_id: str) -> Optional[Game]:
        return self._games.get(game_id)

    def find_all(self) -> List[Game]:
        return list(self._games.values())
```

```python
class MemoryUserRepository(UserRepository):
    def __init__(self):
        self._users: dict[str, User] = {}

    def save(self, user: User) -> None:
        self._users[user.username] = user

    def find_by_username(self, username: str) -> Optional[User]:
        return self._users.get(username)
```

**Por qué está encapsulado:** nadie fuera del repositorio accede al diccionario. El servicio solo usa `save`, `find_by_id`, `find_all`; así se puede cambiar a SQL sin tocar el dominio.

### 8.2 Consecuencias del estado en memoria

| Hecho | Consecuencia |
| --- | --- |
| El estado vive en el proceso | Reiniciar el servidor borra usuarios y partidas. |
| Cada worker tiene su propio diccionario | Dos workers verían partidas distintas. |
| Cada Pod tiene su propia memoria | Dos réplicas verían partidas distintas. |
| No hay transacciones | En un entorno multihilo/multiproceso podría haber carreras. |
| No hay persistencia | No se puede consultar una partida después de un reinicio. |
| El despliegue usa 1 réplica y 1 worker | Se evita el problema, a costa de no escalar horizontalmente. |

**Frase:** “El estado en memoria no es un olvido: es una decisión de alcance. Para dos jugadores y una demo es suficiente, y el patrón repositorio deja preparado el cambio a una base de datos. La contrapartida es que el proyecto es stateful y no puede escalar con varias réplicas sin compartir estado.”

### 8.3 ¿La aplicación es stateless?

Hay que distinguir dos cosas:

- **Autenticación:** es **stateless**. El servidor no guarda sesiones; el token firmado se verifica en cada request. Esto cumple la restricción de REST.
- **Estado del juego:** es **stateful**. Las partidas y usuarios viven en memoria. REST no prohíbe que el servidor tenga recursos; lo que prohíbe es depender de una sesión de conversación. Cada request sigue trayendo su token y el ID del recurso.

**Respuesta corta:** “La autenticación es stateless; el almacenamiento del juego es stateful. Son cosas distintas.”

### 8.4 Concurrencia

En el despliegue actual:

- Flask local: `app.run(..., threaded=False)` → atiende una petición a la vez.
- Gunicorn: `--workers 1` con worker síncrono → también serializa las peticiones.

Eso evita carreras en `join` y `play`: dos jugadores no pueden ejecutar el “check-then-act” al mismo tiempo. Es una forma simple de consistencia, pero limita el rendimiento.

**Riesgos si se escala sin cambiar nada:**

- Dos jugadores podrían unirse a la vez y superar el límite de dos.
- Dos intentos podrían leer el mismo turno y ambos pasar la validación.
- Dos workers podrían generar el mismo ID si ambos consultan antes de guardar.
- Un jugador podría ver un estado distinto según el Pod al que llegue.

**Soluciones futuras:**

- Base de datos con transacciones y una restricción única para el ID.
- Bloqueo pesimista (`SELECT ... FOR UPDATE`) o control de concurrencia optimista con versión.
- Redis o base de datos para el estado compartido.
- Una sola fuente de verdad para el turno.
- Si se usan varias réplicas, una clave de firma común y sesiones/estado compartidos.

### 8.5 Evolución a base de datos

Un esquema razonable:

```sql
users(username PRIMARY KEY, created_at)
games(id PRIMARY KEY, creator, status, turn, winner, created_at)
players(game_id REFERENCES games, username REFERENCES users, secret, PRIMARY KEY(game_id, username))
attempts(id, game_id, player, guess, fijas, picas, created_at)
```

Puntos clave:

- `games.id` con `UNIQUE` para que la colisión se resuelva en la base, no solo en memoria.
- `players` con clave compuesta `(game_id, username)` para evitar duplicados.
- `secret` en una tabla separada o cifrada; nunca en la respuesta.
- Transacción al unirse y al jugar.
- `attempts` con índice por `game_id`.
- Migraciones con Alembic.
- Para escalar, PostgreSQL; para estado compartido rápido, Redis.

**Frase:** “No implementé la base de datos, pero el diseño ya tiene el punto de extensión: `GameRepository` y `UserRepository`. Cambiar la implementación no obliga a tocar `Game` ni `GameService`.”

---

## 9. Frontend y experiencia de usuario

### 9.1 Tecnología

Todo está en `app/templates/index.html`:

- HTML semántico.
- CSS embebido, responsive básico.
- JavaScript vanilla, sin frameworks ni build.
- `fetch` para la API.
- Polling con `setInterval`.

**Por qué:** menos dependencias, más fácil de desplegar y de explicar; para una sola pantalla no se justifica React/Vue.

### 9.2 Vistas

| Vista | Cuándo se muestra | Elementos |
| --- | --- | --- |
| **Login** | Al inicio o tras cerrar sesión. | Nombre, botón Entrar. |
| **Lobby** | Después del login. | Crear partida, **Disponibles**, **Terminadas**. |
| **Unirse** | Al pulsar “Unirme” en una partida `waiting`. | Número secreto, botón Unirme. |
| **Partida** | Al crear, unirse o abrir una partida propia. | Estado, turno, formulario de intento, historial. |
| **Resultado** | Cuando `status === "finished"`. | Ganador, historial, botón Volver. |

### 9.3 Flujo del usuario

1. `POST /login` → guarda `token` y `username` en variables JS.
2. `GET /juego` → renderiza el lobby.
3. Crear: `POST /juego` → `show(game)` → vista de partida.
4. Unirse: `PUT /juego/{id}` → `show(game)`.
5. Jugar: `POST /juego/{id}/jugar` → `GET /juego/{id}` → actualiza.
6. Volver: `lobby()` → `GET /juego` → renderiza.
7. Cerrar sesión: limpia variables y vuelve al login.

### 9.4 Lobby: Disponibles y Terminadas

```js
const available = games
  .filter((game) => game.status !== "finished")
  .sort((a, b) => (a.status === "waiting" ? 0 : 1) - (b.status === "waiting" ? 0 : 1));

const finished = games.filter((game) => game.status === "finished");
```

- **Disponibles** incluye `waiting` e `in_progress`; las `waiting` se ordenan primero.
- **Terminadas** incluye solo `finished`.
- Cada tarjeta muestra estado, ID, creador, jugadores y ganador si existe.
- El botón cambia según el estado: “Unirme”, “Acceder a mi partida”, “Ver resultado”, “Partida llena” o “Partida terminada”.
- Si no hay partidas, muestra un texto vacío en vez de una sección en blanco.

### 9.5 Polling cada 2 segundos

**Partida:**

```js
function startPolling() {
  stopPolling();
  timer = setInterval(refreshRound, 2000);
}

async function refreshRound() {
  if (!current || busy || current.status === "finished") return;
  if (document.visibilityState !== "visible") return;
  try { show(await api(path(current.id)), true); }
  catch (_) { /* se reintenta en el siguiente ciclo */ }
}
```

**Lobby:**

```js
async function refreshLobby() {
  if (!token || busy || lobbyLoading || current || el("lobby").hidden) return;
  if (document.visibilityState !== "visible") return;
  // ...
}
```

**Detalles de calidad:**

- `busy` evita peticiones superpuestas mientras el usuario envía algo.
- `lobbyLoading` evita dos fetches del lobby a la vez.
- `document.visibilityState !== "visible"` evita gastar peticiones con la pestaña oculta.
- `lastGames` compara el JSON y evita re-renderizar si nada cambió.
- Al terminar la partida, `stopPolling()`.
- Al volver al lobby, se detiene el polling de la partida y arranca el del lobby.

**Por qué 2 segundos:** es un compromiso entre frescura y carga. Para dos jugadores es suficiente; el peor caso de latencia es 2 s. Una alternativa sería WebSocket/SSE, pero añade complejidad de conexión, reconexión y estado.

### 9.6 Navegación con hash

- `#/partidas` → lobby.
- `#/partidas/{id}` → partida.
- `#/unirme/{id}` → invitación para unirse.
- `popstate` permite usar atrás/adelante del navegador.
- `history.pushState` no recarga la página.

**Ventaja:** no hace falta un router ni un servidor que sirva rutas del front; todo es una sola página.

### 9.7 Manejo de errores en el front

```js
async function api(url, method = "GET", body) {
  const headers = {};
  if (body) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = "Bearer " + token;
  const response = await fetch(url, { method, headers, body: JSON.stringify(body) });
  const data = await response.json();
  if (!response.ok) throw new Error(data.description || data.error);
  return data;
}
```

- `action()` captura la excepción y la muestra en `#message`.
- El mensaje usa `textContent`, no `innerHTML`, para evitar XSS.
- Si el servidor responde HTML (por ejemplo un `500` no controlado), `response.json()` falla; sería una mejora normalizar todos los errores a JSON.

### 9.8 Accesibilidad y detalles

- `label for` en los inputs.
- `role="status"` en el mensaje.
- `aria-label` en el historial.
- `tabindex="-1"` y `focus()` al abrir una partida.
- `pattern="[0-9]{4}"` y `inputmode="numeric"` en los números.
- `type="password"` para que el número secreto no se vea en pantalla.
- `hidden` para mostrar/ocultar vistas.
- `window.scrollTo` al cambiar de vista.

### 9.9 Límites del frontend

- No usa `localStorage`: recargar la página cierra la sesión.
- No hay reconexión explícita; el polling reintenta en el siguiente ciclo.
- No hay notificaciones push.
- No hay chat ni revancha.
- No hay tests de UI completos; se hizo una verificación con jsdom.
- No hay internacionalización.
- No hay manejo offline.

**Frase:** “El frontend es deliberadamente simple: una sola página, `fetch` y polling. Para el alcance del proyecto prioricé claridad y facilidad de despliegue sobre un framework o WebSocket.”

---

## 10. Docker: cómo se ejecuta y cómo se dockerizaría

### 10.1 Lo que realmente hace el proyecto

El proyecto **no tiene Dockerfile** en el repositorio. En Kubernetes:

- Usa la imagen oficial `python:3.12-slim`.
- Un `initContainer` con `alpine/git:latest` clona el repositorio público en un volumen `emptyDir`.
- El contenedor `web` monta ese volumen, instala `requirements.txt` + Gunicorn y arranca:

```bash
pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0
exec gunicorn --bind 0.0.0.0:5000 --workers 1 run:app
```

**Por qué se hizo así:**

- No requiere publicar una imagen propia en Docker Hub.
- Usa imágenes públicas, ideal para Killercoda.
- Permite actualizar el código haciendo `git push` y reiniciando el Pod.
- Mantiene el repositorio simple.

**Contras:**

- El arranque depende de GitHub y PyPI.
- Es más lento: instala dependencias en cada inicio.
- No es inmutable: el Pod toma el `HEAD` de la rama, no un commit fijo.
- Las etiquetas `alpine/git:latest` y `python:3.12-slim` son mutables.
- No hay build reproducible ni caché de capas.

### 10.2 Dockerfile propuesto para Flask

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

**Explicación:**

| Instrucción | Por qué |
| --- | --- |
| `FROM python:3.12-slim` | Imagen oficial y liviana, alineada con el despliegue. |
| `ENV ...` | No genera `.pyc` y no bufferiza logs. |
| `WORKDIR /app` | Directorio de trabajo. |
| `COPY requirements.txt .` | Copia solo dependencias primero para cachear. |
| `RUN pip install ...` | Instala Flask y Gunicorn en la imagen. |
| `COPY run.py .` / `COPY app ./app` | Copia el código. |
| `useradd` + `USER` | No corre como root. |
| `EXPOSE 5000` | Documenta el puerto. |
| `CMD` exec | Gunicorn recibe señales correctamente. |
| `--workers 1` | Estado en memoria; un solo worker. |

**Construir y ejecutar:**

```bash
docker build -t picas-y-fijas:1.0 .
docker run --rm -p 8080:5000 -e PICAS_SECRET_KEY=clave-segura picas-y-fijas:1.0
# Abrir http://localhost:8080
```

**Con Compose:**

```yaml
services:
  picas:
    build: .
    ports:
      - "8080:5000"
    environment:
      PICAS_SECRET_KEY: "clave-segura"
```

```bash
docker compose up -d --build
docker compose logs -f
docker compose down
```

### 10.3 Comparación con el Dockerfile de clase (Node)

El Dockerfile de clase es:

```dockerfile
FROM node:26-alpine3.22
WORKDIR /app
RUN npm init -y \
 && npm install express --omit=dev \
 && npm pkg set scripts.start="node server.js"
COPY . .
EXPOSE 3000
USER node
CMD ["npm", "start"]
```

**Qué tiene bien:** usuario no root, `EXPOSE`, `CMD` exec, imagen Alpine liviana.

**Qué se puede mejorar:** copiar `package.json` antes del código para cachear; usar `npm ci`; agregar `.dockerignore`; fijar una versión LTS; usar `CMD ["node","server.js"]` para que Node sea PID 1.

**Si el profesor pide “dockerice el servidor de clase”,** esa versión mejorada es:

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY . .
USER node
EXPOSE 3000
CMD ["node", "server.js"]
```

> La versión mejorada requiere `package.json` y `package-lock.json` versionados. Si no existen, se puede usar la versión de clase, que los genera durante el build, o crear el `package.json` antes de construir la imagen.

### 10.4 Preguntas de Docker que pueden salir

| Pregunta | Respuesta |
| --- | --- |
| ¿Imagen vs contenedor? | Imagen = plantilla de solo lectura; contenedor = instancia en ejecución. |
| ¿Qué hace `EXPOSE`? | Documenta el puerto; no lo publica. Se publica con `-p`. |
| ¿Qué hace `-p 8080:5000`? | Mapea el puerto 8080 del host al 5000 del contenedor. |
| ¿Por qué `0.0.0.0`? | Para aceptar conexiones desde fuera del contenedor; `127.0.0.1` solo acepta locales. |
| ¿Por qué usuario no root? | Si la app se compromete, el atacante no tiene root en el contenedor. |
| ¿Qué es una capa? | Cada instrucción del Dockerfile; se cachea y acelera rebuilds. |
| ¿Por qué `.dockerignore`? | Evita copiar `node_modules`, `.git`, secretos y basura; reduce tamaño y riesgos. |
| ¿Docker vs VM? | El contenedor comparte el kernel; la VM tiene su propio SO. |

---

## 11. Kubernetes: despliegue paso a paso

### 11.1 Archivos

| Archivo | Contenido |
| --- | --- |
| `killercoda/namespace.yaml` | Namespace `picas-y-fijas`. |
| `killercoda/deployment.yaml` | Deployment con `initContainer` + contenedor `web`. |
| `killercoda/service.yaml` | Service `ClusterIP` puerto 80 → `http` (5000). |
| `killercoda/KILLERCODA.md` | Guía de ejecución y diagnóstico. |

### 11.2 Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: picas-y-fijas
```

**Para qué:** aislar los recursos del proyecto, evitar choques de nombres y poder borrar todo con `kubectl delete namespace picas-y-fijas` si algo queda inconsistente.

### 11.3 Secret

```bash
kubectl apply -f killercoda/namespace.yaml

if ! kubectl -n picas-y-fijas get secret picas-auth >/dev/null 2>&1; then
  kubectl -n picas-y-fijas create secret generic picas-auth \
    --from-literal=signing-key="$(openssl rand -hex 32)"
fi
```

**Para qué:** `PICAS_SECRET_KEY` debe ser la misma para todos los procesos que validan tokens. Si cada Pod generara una clave aleatoria, los tokens de un Pod no servirían en otro. El Secret no se versiona en Git.

**Por qué `if ! ... get secret`:** para que repetir los comandos no falle si el Secret ya existe; se conserva la misma clave.

### 11.4 Deployment completo

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
            requests:
              cpu: "250m"
              memory: "64Mi"
            limits:
              cpu: "500m"
              memory: "128Mi"
          ports:
            - name: http
              containerPort: 5000
          env:
            - name: PICAS_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: picas-auth
                  key: signing-key
          readinessProbe:
            httpGet:
              path: /
              port: http
```

### 11.5 Explicación línea por línea

| Elemento | Para qué |
| --- | --- |
| `replicas: 1` | El estado está en memoria; una réplica evita estados divergentes. |
| `strategy: Recreate` | Durante un despliegue, primero elimina el Pod viejo y luego crea el nuevo. Evita que convivan dos versiones con estados separados. |
| `selector.matchLabels` | Debe coincidir con `template.metadata.labels`; si no, el Deployment no administra sus Pods. |
| `volumes.emptyDir` | Volumen temporal compartido entre `initContainer` y `web`; se borra con el Pod. |
| `initContainers.download-code` | Clona el repositorio público en `/source/repo` antes de arrancar la app. |
| `alpine/git:latest` | Imagen pública con Git; suficiente para el demo. |
| `git fetch --depth=1 ... HEAD` | Descarga solo el último commit de la rama por defecto; rápido y liviano. |
| `git reset --hard FETCH_HEAD` | Deja el código exactamente como está en el remoto. |
| `containers.web` | Contenedor principal de la aplicación. |
| `image: python:3.12-slim` | Imagen oficial de Python 3.12, ligera. |
| `imagePullPolicy: IfNotPresent` | Usa la imagen local si ya está; si no, la descarga. |
| `workingDir: /source/repo` | Ejecuta los comandos desde el código clonado. |
| `pip install ...` | Instala Flask y Gunicorn al arrancar. |
| `exec gunicorn ...` | Reemplaza el shell por Gunicorn para que reciba señales correctamente. |
| `--bind 0.0.0.0:5000` | Escucha en todas las interfaces, necesario dentro del contenedor. |
| `--workers 1` | Un solo proceso para compartir el estado en memoria. |
| `volumeMounts` | Monta el código en `/source`. |
| `resources.requests` | CPU/memoria garantizada para programar el Pod. |
| `resources.limits` | Máximo de CPU/memoria; si se excede memoria, puede ser `OOMKilled`. |
| `ports.name: http` | Nombre lógico del puerto para que el Service use `targetPort: http`. |
| `containerPort: 5000` | Puerto donde escucha Gunicorn. |
| `env.PICAS_SECRET_KEY` | Inyecta la clave de firma desde el Secret. |
| `readinessProbe` | Comprueba `GET /` en el puerto `http`; si falla, el Pod no recibe tráfico. |

### 11.6 Service

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

| Campo | Significado |
| --- | --- |
| `type: ClusterIP` | Solo accesible dentro del clúster; se usa `port-forward` para la demo. |
| `selector.app` | Debe coincidir con los labels de los Pods. |
| `port: 80` | Puerto del Service. |
| `targetPort: http` | Puerto del contenedor, resuelto por el nombre `http` (5000). |

**Si no coincide el selector:** el Service no tiene endpoints y las peticiones fallan. Se diagnostica con:

```bash
kubectl -n picas-y-fijas get endpoints
# Si aparece <none>, el selector no encuentra Pods listos.
```

### 11.7 Aplicar y verificar

```bash
kubectl apply -f killercoda/namespace.yaml
kubectl apply -f killercoda/deployment.yaml
kubectl apply -f killercoda/service.yaml

kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=300s
kubectl -n picas-y-fijas get all
kubectl -n picas-y-fijas get pods -o wide
kubectl -n picas-y-fijas get endpoints
```

**Resultado esperado:** Pod `Running` con `READY 1/1`; Service con endpoints; `rollout status` exitoso.

### 11.8 Abrir la aplicación

```bash
kubectl -n picas-y-fijas port-forward service/picas-y-fijas \
  --address 0.0.0.0 8080:80
```

- `8080` es el puerto local.
- `80` es el puerto del Service.
- `--address 0.0.0.0` permite que Killercoda exponga el puerto en su interfaz **Traffic / Ports**.
- Mantener el comando ejecutándose; si se corta, repetirlo.

**Alternativa de clase:**

```bash
kubectl expose deployment my-app --port=80 --target-port=80 -n unillanos
kubectl port-forward -n unillanos service/mi-servicio --address 0.0.0.0 80:80
```

### 11.9 Actualizar la aplicación

```bash
# 1. Publicar cambios en GitHub
git push origin main

# 2. Actualizar los YAML locales (si cambiaron)
git pull --ff-only

# 3. Aplicar y forzar un nuevo Pod
kubectl apply -f killercoda/deployment.yaml
kubectl apply -f killercoda/service.yaml
kubectl -n picas-y-fijas rollout restart deployment/picas-y-fijas
kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=300s
```

**Importante:** el Pod clona el repositorio desde GitHub, no desde la carpeta local de Killercoda. El `git pull` local solo actualiza los YAML y la documentación; el código que ejecuta el Pod viene del `HEAD` remoto.

**Si se cambia el Secret:** reiniciar el Deployment para que el contenedor tome la nueva variable.

### 11.10 Diagnóstico

| Síntoma | Causa probable | Comando / solución |
| --- | --- | --- |
| `Pending` | Sin recursos, taints, PVC o selector de nodo | `kubectl describe pod` |
| `ImagePullBackOff` | Imagen mal escrita, tag inexistente o registro privado | `describe pod`, revisar imagen |
| `ErrImageNeverPull` | `imagePullPolicy: Never` y la imagen no está en el nodo | Cambiar política o cargar imagen |
| `Init:Error` | Falló `download-code` (GitHub, red) | `logs -c download-code` |
| `Init:CrashLoopBackOff` | El initContainer se reinicia y falla | `logs -c download-code --previous` |
| `CreateContainerConfigError` | Falta el Secret `picas-auth` o la clave `signing-key` | Crear el Secret en el namespace correcto |
| `CrashLoopBackOff` | Falla Gunicorn, pip o el import de la app | `logs`, `logs --previous` |
| `OOMKilled` | Límite de memoria muy bajo | Subir `limits.memory` |
| `READY 0/1` | Readiness probe falla | Revisar path `/`, puerto `http` y logs |
| Service sin respuesta | Selector o `targetPort` mal | `get endpoints`, `describe service` |
| `502/503` | Sin endpoints o app no lista | `get endpoints`, readiness |
| `port-forward` se corta | Proceso terminado o Pod reiniciado | Volver a ejecutar |

**Secuencia de diagnóstico:**

```bash
kubectl -n picas-y-fijas get pods -o wide
kubectl -n picas-y-fijas describe pod POD
kubectl -n picas-y-fijas logs POD -c download-code
kubectl -n picas-y-fijas logs POD -c web
kubectl -n picas-y-fijas logs POD -c web --previous
kubectl -n picas-y-fijas get events --sort-by=.metadata.creationTimestamp
kubectl -n picas-y-fijas get endpoints
```

### 11.11 Rollback: una advertencia importante

`kubectl rollout undo deployment/picas-y-fijas` revierte el **spec del Deployment** (imagen, env, recursos), pero el `initContainer` sigue clonando el `HEAD` actual de GitHub. Por eso, un rollback de Kubernetes **no garantiza** volver al código anterior.

**Para un rollback real:**

- Fijar un commit en el `initContainer`:
  ```bash
  git -C /source/repo fetch --depth=1 https://github.com/... <COMMIT>
  git -C /source/repo reset --hard FETCH_HEAD
  ```
- O construir una imagen inmutable por versión y desplegar `imagen:tag`.
- O usar `git checkout <tag>` en el initContainer.

**Frase:** “El rollback de Kubernetes revierte el manifiesto, no el código que se descarga en tiempo de ejecución. Es una consecuencia de no usar una imagen propia; con una imagen versionada el rollback sería completo.”

### 11.12 Límites del despliegue

- Una réplica y un worker: no hay alta disponibilidad ni escalado horizontal.
- Estado en memoria: al reiniciar el Pod se pierden partidas.
- Sin `livenessProbe`: si la app se cuelga, Kubernetes no la reinicia.
- Sin `startupProbe`: si el arranque es lento, la readiness puede fallar temporalmente.
- Sin HPA, PDB, NetworkPolicy ni Ingress/TLS.
- Tags mutables (`python:3.12-slim`, `alpine/git:latest`).
- Código en `HEAD`, no en un commit fijo.
- Dependencia de GitHub y PyPI en cada arranque.
- Sin observabilidad (métricas, trazas, logs centralizados).

---

## 12. Pruebas y evidencia

### 12.1 Qué se verificó

| Verificación | Qué comprobó |
| --- | --- |
| **57 comprobaciones de API** | Login, token, creación, validación de números, unión, turnos, jugadas, ganador, listado, errores `400/401/403/404/405/415`. |
| **500 identificadores generados** | Formato de 6 dígitos, dígitos distintos, sin cero inicial y sin repetidos entre sí. |
| **Prueba de colisión forzada** | Si el candidato ya existe, el generador reintenta y devuelve uno libre. |
| **Prueba de auto-refresh con jsdom** | El lobby y la partida se actualizan sin pulsar botones. |
| **Prueba en Python 3.12** | La app arranca y responde dentro de un contenedor `python:3.12-slim`, alineado con Kubernetes. |
| **Demostración manual en dos pestañas** | Dos jugadores crean, se unen, juegan, ven el turno y terminan. |

**Transparencia:** estas verificaciones se hicieron con scripts temporales y pruebas manuales; **no hay una suite de tests versionada** en el repositorio. Es una de las mejoras pendientes. No conviene decir “tengo 57 tests” si no están en el repo; mejor: “ejecuté 57 comprobaciones funcionales durante el desarrollo y validé estos casos”.

### 12.2 Matriz de casos que se probaron

| Caso | Resultado esperado |
| --- | --- |
| Login con username | `200` + token |
| Login sin username | `400` |
| Crear sin token | `401` |
| Crear con número válido | `201` + `Location` |
| Crear con 3 dígitos | `400` |
| Crear con 5 dígitos | `400` |
| Crear con repetidos | `400` |
| Crear con letras | `400` |
| Crear con número entero | `400` |
| Unir con username distinto al token | `400` |
| Unir a partida inexistente | `404` |
| Unir a partida llena | `400` |
| Unir dos veces | `400` |
| Jugar sin ser participante | `403` |
| Jugar fuera de turno | `403` |
| Jugar con número inválido | `400` |
| Jugar con 4 fijas | `200`, estado `finished`, ganador |
| Consultar partida ajena | `403` |
| Consultar partida inexistente | `404` |
| Listar partidas | `200`, resumen sin secretos |
| Método incorrecto | `405` JSON |
| `Content-Type` incorrecto | `415` JSON |
| Token vencido | `401` |

### 12.3 Cómo se probó la API

Con `app.test_client()` se puede probar sin levantar un servidor:

```python
import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app(secret_key="clave-de-prueba")
    app.config["TESTING"] = True
    return app.test_client()


def login(client, username):
    response = client.post("/login", json={"username": username})
    return response.get_json()["token"]


def test_create_game_requires_auth(client):
    response = client.post("/juego", json={"number": "4271"})
    assert response.status_code == 401


def test_full_game(client):
    ana = login(client, "ana")
    luis = login(client, "luis")
    h_ana = {"Authorization": f"Bearer {ana}"}
    h_luis = {"Authorization": f"Bearer {luis}"}

    created = client.post("/juego", json={"number": "4271"}, headers=h_ana)
    assert created.status_code == 201
    game_id = created.get_json()["id"]

    joined = client.put(
        f"/juego/{game_id}",
        json={"username": "luis", "number": "0123"},
        headers=h_luis,
    )
    assert joined.status_code == 200

    game = client.get(f"/juego/{game_id}", headers=h_ana).get_json()
    turn = game["turn"]
    current = h_ana if turn == "ana" else h_luis
    guess = "0123" if turn == "ana" else "4271"

    result = client.post(
        f"/juego/{game_id}/jugar",
        json={"number": guess},
        headers=current,
    )
    assert result.status_code == 200
    assert result.get_json()["fijas"] == 4

    final = client.get(f"/juego/{game_id}", headers=h_ana).get_json()
    assert final["status"] == "finished"
    assert final["winner"] == turn
```

**Por qué funciona:** cada test crea una app nueva con repositorios en memoria; no hay estado compartido entre tests. `secret_key` fijo permite verificar tokens.

### 12.4 Pruebas de identificadores

Se generaron 500 IDs y se comprobó:

- longitud 6;
- todos los dígitos distintos;
- primer dígito distinto de `0`;
- sin duplicados en el conjunto.

También se forzó una colisión: se hizo que el generador devolviera un ID ya usado y se verificó que el bucle lo descartara y pidiera otro. Eso cubre el camino feliz y el camino de colisión.

### 12.5 Prueba de auto-refresh

Con jsdom se simuló el DOM y se comprobó que:

- el lobby consulta `/juego` cada 2 segundos;
- una partida nueva aparece sin recargar;
- el turno y los intentos se actualizan;
- al terminar, se detiene el polling.

**Frase:** “La prueba de jsdom no reemplaza una prueba end-to-end en navegador, pero verifica la lógica de polling y renderizado sin depender de un navegador real.”

### 12.6 Prueba en Python 3.12

El entorno local puede tener otra versión, pero la imagen de Kubernetes es `python:3.12-slim`. Se ejecutó la app en esa versión para detectar incompatibilidades. Esto es importante porque el proyecto declara Python 3.12 en el README y en el Dockerfile propuesto.

### 12.7 Qué falta en pruebas

- Suite `pytest` versionada.
- Cobertura de ramas.
- Pruebas de token vencido con reloj simulado.
- Pruebas de concurrencia real (varios hilos/procesos).
- Pruebas end-to-end con Playwright/Selenium.
- Pruebas de carga (muchos jugadores).
- Pruebas de Kubernetes (Kind/Minikube) automatizadas.
- CI con GitHub Actions.

**Si preguntan “¿cómo mejorarías las pruebas?”:** esta lista es la respuesta.

---

## 13. Decisiones de diseño y trade-offs

| Decisión | Por qué | Costo / límite | Alternativa |
| --- | --- | --- | --- |
| **Flask** | Simple, legible, ideal para una API pequeña; el proyecto ya estaba en Python. | Menos “baterías incluidas” que Django; servidor de desarrollo para local. | Express, FastAPI, Django. |
| **REST + JSON** | El cliente es un navegador; JSON es nativo; recursos claros; fácil de probar con cURL. | Acciones como “jugar” no son REST puro. | RPC/gRPC, GraphQL. |
| **Estado en memoria** | Cero dependencias externas; rápido de levantar; suficiente para dos jugadores. | No persiste, no escala horizontalmente, se pierde al reiniciar. | SQLite, PostgreSQL, Redis. |
| **Polling cada 2 s** | Simple; no requiere WebSocket ni infraestructura de tiempo real. | Latencia de hasta 2 s; peticiones periódicas. | WebSocket, SSE, long polling. |
| **Token firmado** | Sin estado, sin tabla de sesiones; `itsdangerous` ya es dependencia de Flask. | No se revoca; no hay refresh; no es JWT estándar. | JWT, sesiones con Redis. |
| **IDs de 6 dígitos** | Legibles y fáciles de compartir; 136.080 combinaciones. | Enumerables; no son un secreto. | UUID, ULID, consecutivo. |
| **Arquitectura en capas** | Separa HTTP, casos de uso, reglas y almacenamiento; testeable. | Más archivos y más ceremonia para un proyecto pequeño. | Monolito en un archivo. |
| **1 réplica / 1 worker** | Evita estados divergentes. | Sin alta disponibilidad ni escalado. | Estado compartido + varias réplicas. |
| **initContainer + imagen oficial** | No requiere publicar imagen; fácil en Killercoda. | Arranque lento, dependencia de red, código no inmutable. | Dockerfile + registro de imágenes. |
| **JavaScript vanilla** | Sin build, sin dependencias, fácil de desplegar. | Menos estructura para crecer. | React, Vue, Svelte. |
| **`400` para transiciones inválidas** | Unifica el contrato y simplifica el manejo. | `409 Conflict` sería más preciso para partida llena o jugador duplicado. | `409` en conflictos de estado. |
| **`PUT` para unirse** | Actualiza la partida con el segundo jugador; viene del contrato de clase. | No es idempotente en la práctica; semánticamente es una acción. | `POST /juego/{id}/jugadores`. |
| **Login sin contraseña** | Alcance académico; identifica al jugador por nombre. | Cualquiera puede suplantar a otro; no es autenticación fuerte. | Password hash + JWT/sesión. |
| **Un solo idioma (español)** | El usuario y el curso son en español. | No hay i18n. | Archivos de traducción. |

### 13.1 “¿Por qué REST y no RPC?”

Porque el cliente principal es un navegador, el formato natural es JSON y los recursos se modelan bien con URLs. REST es más simple de consumir, cachear y depurar con cURL. RPC/gRPC sería mejor si hubiera comunicación interna entre microservicios, alto rendimiento, streaming o un contrato binario fuerte. El proyecto no necesita nada de eso.

**Si el profesor pide RPC:** se puede mapear la API a un `.proto`:

| REST | RPC |
| --- | --- |
| `POST /login` | `AuthService.Login` |
| `POST /juego` | `JuegoService.CrearJuego` |
| `PUT /juego/{id}` | `JuegoService.Unirse` |
| `POST /juego/{id}/jugar` | `JuegoService.Jugar` |
| `GET /juego/{id}` | `JuegoService.VerJuego` |
| `GET /juego` | `JuegoService.ListarJuegos` |

### 13.2 “¿Por qué no usó una base de datos?”

Porque el alcance era una demo funcional de dos jugadores y el estado en memoria elimina dependencias externas. La arquitectura ya está preparada: los servicios dependen de interfaces de repositorio, no de diccionarios. Cambiar a PostgreSQL es implementar `PostgresGameRepository` y `PostgresUserRepository`, y cambiar el composition root. La base de datos sería obligatoria para persistencia, varias réplicas y concurrencia real.

### 13.3 “¿Por qué no usó WebSocket?”

Porque el polling cada 2 segundos es suficiente para dos jugadores y evita manejar conexiones, reconexión, heartbeats y estado del socket. WebSocket sería mejor para muchos jugadores, chat o latencia baja. Una solución intermedia sería SSE.

### 13.4 “¿Por qué no usó JWT?”

`itsdangerous` ya viene con Flask, permite firmar y expirar tokens sin agregar dependencias. JWT es un estándar y facilita interoperabilidad, pero para este proyecto el token firmado cumple la misma función básica: identificar al usuario sin estado. Si se necesitara integración con otros servicios, JWT sería preferible.

### 13.5 “¿Por qué no usó microservicios?”

Porque el juego es pequeño y un monolito en capas es más fácil de desarrollar, desplegar y depurar. Los microservicios agregarían latencia de red, consistencia distribuida, observabilidad y complejidad operativa sin un beneficio claro para dos jugadores. La separación por capas ya permite extraer un servicio si crece.

### 13.6 “¿Qué fue lo más difícil?”

Una respuesta honesta: **el estado y la concurrencia**. Mantener el turno, evitar que dos jugadores jueguen a la vez y garantizar que ambos vean lo mismo fue más delicado que la interfaz. La solución actual (un worker y una réplica) es simple y correcta para la demo, pero es el punto que primero cambiaría con una base de datos y transacciones. Otra dificultad fue el despliegue: el `initContainer`, el Secret y el `port-forward` tienen varios modos de fallar, y por eso documenté el diagnóstico.

---

## 14. Limitaciones y trabajo futuro

### 14.1 Limitaciones actuales

| Limitación | Impacto | Prioridad |
| --- | --- | --- |
| Estado en memoria | Se pierde todo al reiniciar; no escala horizontalmente. | Alta |
| Una réplica / un worker | Sin alta disponibilidad; cuello de botella. | Alta |
| Sin tests versionados | Menos confianza al cambiar el código. | Alta |
| Sin Dockerfile propio | Arranque lento, dependencia de GitHub/PyPI, código no inmutable. | Media |
| Sin HTTPS | El token viaja en claro; inseguro fuera de localhost. | Alta en producción |
| Sin contraseña | Cualquiera puede entrar con cualquier nombre. | Alta en producción |
| Sin revocación de token | Un token copiado sirve hasta vencer. | Media |
| Sin rate limiting | Se puede abusar de login o probar IDs. | Media |
| Sin `livenessProbe` | Un proceso colgado no se reinicia. | Media |
| Sin Ingress/TLS | Solo se accede por `port-forward`. | Media |
| Sin observabilidad | No hay métricas, trazas ni logs centralizados. | Media |
| Sin paginación en `GET /juego` | El lobby crece sin límite. | Baja |
| Sin timestamps | No se sabe cuándo se creó/jugó. | Baja |
| Sin chat/revancha | Funcionalidad limitada al juego básico. | Baja |
| Sin i18n | Solo español. | Baja |
| `500` no JSON | Un error inesperado rompe el contrato JSON. | Media |
| Username sin límites | Nombres vacíos con espacios o muy largos. | Baja |
| IDs enumerables | No son secretos; la autorización está en el token. | Baja |

### 14.2 Roadmap priorizado

**Corto plazo (lo que haría primero):**

1. **Persistencia con SQLite/PostgreSQL.** Implementar repositorios SQL, migraciones y transacciones. Es la mejora con mayor impacto.
2. **Tests con pytest + CI.** Versionar la suite, cubrir errores y flujo completo, ejecutar en GitHub Actions.
3. **Dockerfile propio + imagen versionada.** Construir, etiquetar y publicar; cambiar el Deployment a `image: ghcr.io/...:tag`; eliminar el `initContainer`.
4. **Handler JSON para `500`.** Agregar `@app.errorhandler(Exception)` con log y ID de correlación.
5. **Validar username.** `strip()`, longitud máxima, caracteres permitidos.

**Mediano plazo:**

6. **HTTPS + Ingress.** Certificado TLS, host, reglas de path.
7. **Rate limiting.** En login y en jugar; por IP/usuario.
8. **Contraseña + hash.** Argon2/bcrypt, registro/login, recuperación.
9. **Revocación/refresh de tokens.** Lista negra o rotación; refresh token.
10. **Observabilidad.** Logs estructurados, métricas Prometheus, trazas OpenTelemetry.
11. **WebSocket/SSE.** Actualización en tiempo real; menos carga que polling.
12. **Paginación y filtros en el lobby.**

**Largo plazo:**

13. **Múltiples réplicas con estado compartido.** PostgreSQL + Redis; eliminar `Recreate`; usar `RollingUpdate`.
14. **HPA, PDB, NetworkPolicy.** Escalado, disponibilidad y seguridad de red.
15. **Revancha, chat, espectadores, historial.**
16. **Internacionalización y temas.**
17. **Pruebas de carga y caos.**
18. **Documentación OpenAPI/Swagger.**

### 14.3 Cómo escalar a varias réplicas

El cambio no es solo `replicas: 3`. Hay que resolver:

| Problema | Solución |
| --- | --- |
| Cada Pod tiene partidas distintas | Estado compartido en PostgreSQL/Redis. |
| Cada Pod tiene usuarios distintos | Tabla de usuarios compartida. |
| Cada Pod tiene su propia clave | Secret común `PICAS_SECRET_KEY`. |
| Dos jugadores pueden unirse a la vez | Transacción + restricción única. |
| Dos jugadores pueden jugar a la vez | Bloqueo/optimistic locking sobre el turno. |
| El polling puede caer en cualquier Pod | Service balancea; el estado es compartido. |
| Despliegue con dos versiones | `RollingUpdate` + compatibilidad de esquema. |
| Sesiones locales | No hay sesiones; el token es stateless. |

**Frase:** “El proyecto es un monolito stateful. Para escalar hay que convertirlo en stateless o compartir el estado. La autenticación ya es stateless; el juego no.”

---

## 15. Guion de demostración

### 15.1 Antes de empezar

- [ ] Servidor local corriendo (`python -m run`) **o** `port-forward` activo.
- [ ] Dos pestañas o dos navegadores listos.
- [ ] Nombres de prueba decididos: `ana` y `luis`.
- [ ] Números secretos de prueba: `4271` y `0123`.
- [ ] Token/curl listos para mostrar la API.
- [ ] Terminal con `kubectl` lista (si se va a mostrar Kubernetes).
- [ ] Plan B: si Kubernetes falla, mostrar local y explicar el YAML.
- [ ] No mostrar el número secreto en pantalla si hay público; usar `type="password"`.

**Consejo:** no dependas de una partida ya existente. Crea una nueva durante la demo. Si el servidor se reinició, las partidas viejas desaparecieron; es una oportunidad para explicar la limitación de memoria.

### 15.2 Guion de 8 a 10 minutos

#### Minuto 0–1: contexto

Di:

> “Picas y Fijas es un juego de dos jugadores. Cada uno elige cuatro dígitos distintos y, por turnos, intenta adivinar el número del otro. Una fija es dígito y posición correctos; una pica es dígito correcto en otra posición. Gana quien llega a cuatro fijas. La aplicación tiene frontend web, API REST en Flask y despliegue en Kubernetes.”

Muestra el repositorio y la estructura de carpetas:

```text
app/
  domain/       reglas
  services/     casos de uso
  repositories/ almacenamiento
  routes/       HTTP
  templates/    frontend
killercoda/     Kubernetes
run.py
requirements.txt
```

#### Minuto 1–2: login y lobby

1. Abre `http://localhost:5000` (o `http://localhost:8080`).
2. Entra como `ana`.
3. Señala:
   - “El login devuelve un token firmado; se guarda en memoria de la pestaña.”
   - “El lobby tiene **Disponibles** y **Terminadas**.”
   - “Se actualiza solo cada 2 segundos.”

#### Minuto 2–3: crear partida

1. En la pestaña de `ana`, escribe el secreto `4271`.
2. Pulsa **Crear partida**.
3. Señala el estado “Sin completar”, el ID de 6 dígitos y el mensaje “Espera a que otro jugador se una”.

Di:

> “El ID se genera con seis dígitos distintos, sin cero inicial, y se verifica que no exista. Hay 136.080 combinaciones posibles.”

#### Minuto 3–4: unirse desde la segunda pestaña

1. En otra pestaña, entra como `luis`.
2. En **Disponibles**, busca la partida de `ana` y pulsa **Unirme**.
3. Escribe el secreto `0123`.
4. Pulsa **Unirme**.

Di:

> “Al unirse el segundo jugador, el servidor sortea el turno y la partida pasa a `in_progress`. El primer jugador ve el cambio automáticamente sin recargar.”

**Demuestra el auto-refresh:** deja la pestaña de `ana` quieta; en menos de 2 segundos debe aparecer el turno y el formulario de juego (si le tocó a ella).

#### Minuto 4–7: jugar

El turno es aleatorio. Adapta el guion:

**Si empieza `ana`:**

| Turno | Jugador | Intento | Resultado esperado |
| --- | --- | --- | --- |
| 1 | Ana | `1234` | 0 fijas, 3 picas |
| 2 | Luis | `5678` | 1 fija, 0 picas |
| 3 | Ana | `0132` | 2 fijas, 2 picas |
| 4 | Luis | `4271` | 4 fijas, gana Luis |

**Si empieza `luis`:**

| Turno | Jugador | Intento | Resultado esperado |
| --- | --- | --- | --- |
| 1 | Luis | `1234` | 1 fija, 2 picas |
| 2 | Ana | `1234` | 0 fijas, 3 picas |
| 3 | Luis | `4271` | 4 fijas, gana Luis |

> Los resultados de la tabla están calculados para los secretos `4271` (Ana) y `0123` (Luis). Si usas otros números, no los presentes como si fueran estos.

Mientras juegas, explica:

- “El servidor valida que sea el turno; si no, responde `403`.”
- “El número secreto nunca se envía al cliente.”
- “Cada intento se guarda en el historial.”
- “Al llegar a 4 fijas, el estado cambia a `finished` y se define el ganador.”

**Si quieres mostrar un error:** en la pestaña que no tiene el turno, el formulario está oculto. Usa cURL para mostrar `403`:

```bash
curl -i -X POST http://localhost:5000/juego/ID/jugar \
  -H "Authorization: Bearer TOKEN_QUE_NO_JUEGA" \
  -H 'Content-Type: application/json' \
  -d '{"number":"1234"}'
```

O muestra un `400` con dígitos repetidos:

```bash
curl -i -X POST http://localhost:5000/juego \
  -H "Authorization: Bearer $TOKEN_ANA" \
  -H 'Content-Type: application/json' \
  -d '{"number":"1123"}'
```

#### Minuto 7–8: terminar y volver al lobby

1. Cuando alguien gane, muestra el mensaje “Ganó …”.
2. Pulsa **Volver a la sala**.
3. Señala que la partida aparece en **Terminadas** y ya no en **Disponibles**.
4. Cierra sesión y muestra que vuelve al login.

Di:

> “El lobby separa disponibles y terminadas. Las terminadas quedan visibles para consultar el resultado.”

#### Minuto 8–9: API con cURL

Muestra una petición y una respuesta:

```bash
curl -i -X POST http://localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"ana"}'
```

```bash
curl -i http://localhost:5000/juego \
  -H "Authorization: Bearer $TOKEN"
```

Señala:

- `Content-Type` y `Authorization`.
- Códigos `200`, `201`, `400`, `401`, `403`, `404`.
- Errores JSON.

#### Minuto 9–10: Kubernetes

Muestra los archivos y comandos:

```bash
kubectl -n picas-y-fijas get all
kubectl -n picas-y-fijas get pods -o wide
kubectl -n picas-y-fijas get endpoints
```

Explica:

- “Namespace aísla.”
- “Secret guarda la clave de firma.”
- “initContainer clona el código; emptyDir lo comparte.”
- “web instala dependencias y arranca Gunicorn con un worker.”
- “Service ClusterIP en 80 → targetPort http (5000).”
- “port-forward es para la demo, no para producción.”
- “Una réplica y un worker porque el estado es en memoria.”

#### Cierre

> “El proyecto cumple el flujo completo: dos jugadores, reglas, API REST, autenticación y despliegue. La limitación principal es el estado en memoria; la siguiente mejora es persistencia con PostgreSQL, tests automatizados e imagen Docker propia.”

### 15.3 Plan B si algo falla

| Falla | Qué hacer |
| --- | --- |
| El servidor local no responde | Revisar que `python -m run` esté corriendo; reiniciar. |
| El puerto 5000 está ocupado | Cambiar el puerto en `run.py` o liberar el proceso. |
| La página no carga en K8s | Revisar `get pods`, `get endpoints`, `port-forward`. |
| El Pod está en `CrashLoopBackOff` | `kubectl logs`; si es por dependencias, revisar red/PyPI. |
| El Pod está en `CreateContainerConfigError` | Crear el Secret en el namespace correcto. |
| El token venció | Volver a iniciar sesión. |
| Se perdió la partida | El servidor se reinició; crear una nueva y explicar la limitación. |
| El navegador muestra datos viejos | Recargar; el polling debería actualizar, pero un refresh fuerza. |
| `port-forward` se cortó | Volver a ejecutarlo. |
| No hay internet en Killercoda | El initContainer y pip fallan; usar local o una imagen preconstruida. |

### 15.4 Frases que puedes usar durante la demo

- “El cliente nunca ve el número secreto; solo ve sus intentos y los del rival.”
- “El token está firmado, no cifrado: el username se puede leer, pero no modificar.”
- “El lobby se actualiza por polling cada 2 segundos; no es WebSocket, es una decisión de simplicidad.”
- “El Service no publica la app a Internet; para la demo uso port-forward.”
- “El estado en memoria explica por qué hay una sola réplica y un solo worker.”
- “Si el Pod se reinicia, las partidas se pierden; es la limitación que primero resolvería con una base de datos.”

---

## 16. Preguntas probables del profesor

> **Estrategia:** responde primero en una frase, luego da el archivo o el ejemplo. No empieces con una explicación larga; el profesor puede interrumpir y preguntar otra cosa.

### 16.1 Proyecto y requisitos

| Pregunta | Respuesta corta |
| --- | --- |
| ¿De qué trata el proyecto? | Juego de dos jugadores que adivinan el número secreto del rival con picas y fijas; incluye frontend web, API REST, autenticación y despliegue en Kubernetes. |
| ¿Qué requisitos cumple? | Dos jugadores, cuatro dígitos distintos, turno, picas/fijas, ganador, lobby, API REST+JSON, autenticación y despliegue. |
| ¿Es un sistema distribuido? | Es una aplicación cliente-servidor distribuida: navegador y servidor son procesos separados que se comunican por HTTP. No es una arquitectura de microservicios. |
| ¿Por qué Flask y no Express/Node? | Flask es simple, legible y el proyecto ya estaba en Python. Express también sería válido; el profesor de clase mostró Node, pero el enunciado no obliga a un lenguaje. |
| ¿Por qué no microservicios? | Para dos jugadores sería sobreingeniería; un monolito en capas es más fácil de desplegar y depurar. La separación por capas permite extraer servicios si crece. |
| ¿Qué parte fue la más difícil? | El estado y la concurrencia: mantener el turno, evitar jugadas simultáneas y que ambos vean lo mismo. La solución actual es un worker y una réplica. |
| ¿Qué aprendiste? | Diseño de API, separación de capas, autenticación stateless, polling, Docker/Kubernetes y diagnóstico de fallos. |
| ¿Qué mejorarías primero? | Persistencia con PostgreSQL, tests automatizados e imagen Docker propia. |

### 16.2 Arquitectura y dominio

| Pregunta | Respuesta corta |
| --- | --- |
| ¿Cuáles son las capas? | Rutas → servicios → dominio → repositorios; `create_app` es el composition root y `index.html` es el cliente. |
| ¿Qué hace cada capa? | Rutas: HTTP y auth; servicios: casos de uso; dominio: reglas; repositorios: almacenamiento. |
| ¿Dónde está la lógica del juego? | En `app/domain/game.py`; no está en las rutas ni en el HTML. |
| ¿Qué es una app factory? | Una función (`create_app`) que crea y configura la app; facilita tests y varias configuraciones. |
| ¿Qué es un blueprint? | Un grupo de rutas con un prefijo; aquí `auth_bp` y `game_bp`. |
| ¿Qué es el composition root? | El lugar donde se conectan repositorios, servicios, rutas y errores; en este proyecto, `create_app`. |
| ¿Qué es repository pattern? | Abstraer el almacenamiento detrás de una interfaz (`save`, `find_by_id`, `find_all`) para poder cambiar la implementación. |
| ¿Qué es inyección de dependencias? | Pasar las dependencias desde afuera (`GameService(game_repo)`) en vez de crearlas dentro; facilita tests y cambios. |
| ¿Qué es un invariante? | Una regla que siempre debe cumplirse: exactamente dos jugadores, cuatro dígitos distintos, un solo turno. |
| ¿Cómo se calculan picas y fijas? | Fija: mismo dígito y posición. Pica: dígito presente en otra posición. `picas = pertenencias − fijas`. |
| ¿Cómo se genera el ID? | Seis dígitos distintos, sin cero inicial, con `secrets`; se verifica que no exista y se reintenta si colisiona. |
| ¿Qué pasa si se agotan los IDs? | Se lanza `RuntimeError`; hay 136.080 combinaciones. En API sería `500`, aunque en la práctica no se llega. |
| ¿Cómo se evita que un jugador vea el secreto? | `to_dict()` no incluye `_secrets`; `GET /juego/{id}` solo permite participantes; la lista no incluye intentos. |
| ¿Qué pasa si un tercero intenta unirse? | `400`: la partida ya tiene dos jugadores. |
| ¿Qué pasa si el creador intenta unirse? | `400`: ya está en la lista de jugadores. |
| ¿Qué pasa si se intenta jugar en una partida terminada? | `400`: la partida no está en juego. |
| ¿Cómo se sortea el turno? | `random.choice(self.players)` al unirse el segundo jugador. No es criptográfico, pero es suficiente para la equidad del juego. |
| ¿Qué pasa si dos jugadores juegan a la vez? | En el despliegue actual, un worker y una réplica serializan las peticiones. Con varias réplicas haría falta una transacción/bloqueo. |

### 16.3 API y autenticación

| Pregunta | Respuesta corta |
| --- | --- |
| ¿Qué es REST? | Estilo arquitectónico basado en recursos, HTTP, stateless e interfaz uniforme. |
| ¿Por qué `PUT` para unirse? | Porque actualiza la partida con el segundo jugador y viene del contrato de clase. Semánticamente sería mejor `POST /juego/{id}/jugadores`; es una deuda de diseño. |
| ¿Por qué `POST` para jugar? | Porque es una acción no idempotente: cada intento cuenta y cambia el turno. |
| ¿401 vs 403? | 401: no autenticado o token inválido/vencido. 403: autenticado pero sin permiso (no participa o no es su turno). |
| ¿404 vs 405? | 404: el recurso/ruta no existe. 405: la ruta existe pero el método HTTP no está permitido. |
| ¿400 vs 409? | 400: entrada o transición inválida. 409 sería más preciso para conflictos de estado (partida llena, jugador duplicado); el proyecto usa 400 por simplicidad. |
| ¿Por qué el número es string? | Para conservar ceros iniciales (`"0123"`) y validar exactamente cuatro caracteres. |
| ¿Por qué `GET /juego` no exige ser participante? | Es el lobby; solo devuelve un resumen público (id, creador, jugadores, estado, ganador). |
| ¿Por qué `GET /juego/{id}` sí exige participante? | Porque incluye intentos y estado detallado de la partida; no debe ser visible para cualquiera. |
| ¿Cómo funciona el token? | `POST /login` firma `{"username":...}` con `itsdangerous`; el cliente lo manda como `Bearer`; el decorador verifica firma y expiración. |
| ¿El token es seguro? | Está firmado, no cifrado: el username se puede leer, pero no modificar. Falta HTTPS y revocación para producción. |
| ¿Cerrar sesión revoca el token? | No; solo borra el token del JavaScript. Un token copiado sigue válido hasta vencer. |
| ¿Por qué guardar el token en una variable y no en `localStorage`? | Para reducir persistencia ante XSS; el costo es que recargar la página cierra la sesión. |
| ¿Por qué no hay CORS? | El front se sirve desde el mismo origen que la API. Si se separara, habría que configurar CORS. |
| ¿Por qué no hay CSRF? | Se usa `Authorization: Bearer`, no cookies de sesión; el navegador no adjunta el token automáticamente. |
| ¿Qué pasa si cambia `PICAS_SECRET_KEY`? | Todos los tokens existentes se invalidan; los usuarios deben volver a entrar. |
| ¿Qué pasa con un `500`? | No hay handler JSON específico; Flask responde HTML. Es una mejora pendiente. |
| ¿Cómo se validan las entradas? | Tipo string, longitud 4, ASCII, dígitos y `len(set(...)) == 4`; el username se valida en login y en unirse. |

### 16.4 Persistencia, concurrencia y escalado

| Pregunta | Respuesta corta |
| --- | --- |
| ¿Por qué estado en memoria? | Cero dependencias, rápido de levantar y suficiente para dos jugadores; el patrón repositorio deja preparado el cambio. |
| ¿Qué pasa al reiniciar el servidor? | Se pierden usuarios y partidas; los tokens también pueden invalidarse si no hay una clave fija. |
| ¿Cómo escalar? | Estado compartido (PostgreSQL/Redis), varias réplicas, clave común, transacciones y quitar `Recreate`. |
| ¿Qué pasa con dos réplicas sin cambios? | Cada Pod tendría partidas distintas; un jugador podría no ver la partida del otro. |
| ¿Cómo sería la base de datos? | Tablas `users`, `games`, `players`, `attempts`; clave única en `games.id`; transacciones al unir/jugar. |
| ¿Cómo se garantiza unicidad del ID? | Hoy con un set en memoria y reintento; en base de datos con `UNIQUE` y reintento ante conflicto. |
| ¿Cómo se maneja la concurrencia? | Hoy un worker/una réplica serializa; mañana transacción + bloqueo pesimista u optimista. |
| ¿Qué pasa si se cae el Pod? | Kubernetes lo recrea; se pierde el estado en memoria y hay que crear otra partida. |
| ¿Qué pasa si GitHub o PyPI fallan? | El `initContainer` o `pip install` fallan; el Pod queda en error. Una imagen propia eliminaría esa dependencia en runtime. |

### 16.5 Frontend

| Pregunta | Respuesta corta |
| --- | --- |
| ¿Cómo se actualiza el lobby? | Polling cada 2 s con `setInterval`; se detiene si la pestaña está oculta, hay una petición en curso o estás en una partida. |
| ¿Por qué 2 segundos? | Compromiso entre frescura y carga; para dos jugadores es suficiente. |
| ¿Por qué no WebSocket? | Añade conexión, reconexión y heartbeats; para este alcance el polling es más simple. |
| ¿Cómo se separan disponibles y terminadas? | `status !== "finished"` y `status === "finished"`; las `waiting` se ordenan primero. |
| ¿Qué pasa al recargar la página? | Se pierde el token (está en una variable JS) y hay que volver a entrar. |
| ¿Cómo se evita XSS? | Se usa `textContent`, no `innerHTML`, para insertar datos del servidor. |

### 16.6 Docker y Kubernetes

| Pregunta | Respuesta corta |
| --- | --- |
| ¿Dónde está el Dockerfile? | El proyecto no tiene uno; usa `python:3.12-slim` y un `initContainer` que clona el código. Si se exige, hay un Dockerfile propuesto en la sección 10. |
| ¿Docker vs VM? | El contenedor comparte el kernel del host; la VM tiene su propio SO. |
| ¿Imagen vs contenedor? | Imagen = plantilla de solo lectura; contenedor = instancia en ejecución. |
| ¿Qué hace `EXPOSE`? | Documenta el puerto; no lo publica. Se publica con `-p`. |
| ¿Por qué `0.0.0.0`? | Para aceptar conexiones desde fuera del contenedor; `127.0.0.1` solo acepta locales. |
| ¿Qué es un Pod? | Unidad mínima de Kubernetes; uno o más contenedores con red y volúmenes compartidos. |
| ¿Qué hace un Deployment? | Mantiene réplicas, gestiona actualizaciones y rollback. |
| ¿Qué hace un Service? | Da IP/DNS estable y balancea hacia los Pods. |
| ¿`port` vs `targetPort`? | `port` es del Service; `targetPort` es del contenedor. |
| ¿ClusterIP vs NodePort vs LoadBalancer? | ClusterIP: interno; NodePort: puerto en cada nodo; LoadBalancer: IP externa del proveedor. |
| ¿Qué es un `initContainer`? | Contenedor que corre antes del principal y debe terminar bien; aquí clona el código. |
| ¿Qué es `emptyDir`? | Volumen temporal que vive mientras el Pod exista; aquí comparte el código entre init y web. |
| ¿Por qué una réplica y un worker? | El estado está en memoria; dos procesos tendrían estados distintos. |
| ¿Por qué `Recreate`? | Evita que durante el despliegue convivan dos versiones con estados separados. |
| ¿Readiness vs liveness? | Readiness saca el Pod de los endpoints si no está listo; liveness reinicia el contenedor si se cuelga. |
| ¿Un Secret es seguro? | No por sí solo: se guarda base64; hay que proteger etcd, usar RBAC y cifrado en reposo. |
| ¿Cómo se actualiza la app? | `git push`, `kubectl apply`, `rollout restart`; el nuevo Pod clona el `HEAD`. |
| ¿El rollback restaura el código? | No necesariamente: `rollout undo` revierte el spec, pero el initContainer sigue clonando el `HEAD`. Para rollback real hay que fijar commit o imagen. |
| ¿Cómo se diagnostica `CrashLoopBackOff`? | `kubectl logs`, `logs --previous`, `describe pod`; revisar comando, env y dependencias. |
| ¿Cómo se diagnostica un Service sin respuesta? | `get endpoints`, `describe service`, revisar selector, `targetPort` y readiness. |
| ¿Qué pasa si falta el Secret? | `CreateContainerConfigError`; se crea el Secret en el namespace correcto. |
| ¿Qué pasa si la app escucha en `127.0.0.1`? | El Service no puede alcanzarla; debe escuchar en `0.0.0.0`. |

### 16.7 RPC

| Pregunta | Respuesta corta |
| --- | --- |
| ¿Qué es RPC? | Llamar una función remota como si fuera local; oculta serialización, red y errores. |
| ¿REST vs RPC? | REST modela recursos; RPC modela acciones. REST es más natural para el navegador; RPC/gRPC para comunicación interna y rendimiento. |
| ¿Por qué no usó RPC? | El cliente es un navegador, JSON es suficiente y no se necesita streaming ni binario. gRPC sería una alternativa, no una obligación. |
| ¿Cómo sería la versión gRPC? | Un `.proto` con `JuegoService` (`CrearJuego`, `Unirse`, `Jugar`, `VerJuego`, `ListarJuegos`), servidor con `grpcio` y cliente con stub. |
| ¿JSON-RPC? | Protocolo JSON con `jsonrpc`, `method`, `params`, `id`; errores `-32600`, `-32601`, `-32602`. |
| ¿Códigos gRPC? | `OK`, `INVALID_ARGUMENT`, `NOT_FOUND`, `PERMISSION_DENIED`, `UNAUTHENTICATED`, `DEADLINE_EXCEEDED`, `UNAVAILABLE`, `UNIMPLEMENTED`. |
| ¿Qué es un deadline? | Tiempo máximo que el cliente espera; evita quedarse colgado. |
| ¿Se reintentan los errores? | Solo operaciones idempotentes y errores transitorios; nunca `INVALID_ARGUMENT` o `PERMISSION_DENIED`. |

### 16.8 Pruebas y mejoras

| Pregunta | Respuesta corta |
| --- | --- |
| ¿Qué probó? | 57 comprobaciones de API, 500 IDs, colisión forzada, auto-refresh con jsdom y ejecución en Python 3.12. |
| ¿Hay tests automatizados? | No versionados; se hicieron scripts temporales. La mejora es una suite `pytest` con `test_client`. |
| ¿Cómo probaría un token vencido? | Crear un token con `max_age` negativo o simular el reloj; verificar `401`. |
| ¿Cómo probaría concurrencia? | Varios hilos/procesos intentando unirse/jugar; con la implementación actual habría que usar una base de datos y transacciones. |
| ¿Qué haría con más tiempo? | Persistencia, tests/CI, Dockerfile, HTTPS, rate limiting, WebSocket y observabilidad. |

### 16.9 Respuestas largas para preguntas difíciles

#### “Explique la arquitectura en 30 segundos”

> “Es una aplicación en capas. El navegador llama una API REST en Flask. Las rutas solo traducen HTTP y verifican el token. Los servicios coordinan los casos de uso. El dominio `Game` contiene las reglas: validación, turno, picas, fijas y ganador. Los repositorios encapsulan el almacenamiento en memoria. `create_app` conecta todo. Esa separación permite probar el dominio sin Flask y cambiar la persistencia sin tocar las reglas.”

#### “¿Por qué dice que es distribuido si todo corre en un Pod?”

> “La distribución está en la comunicación: el navegador de cada jugador es un proceso separado del servidor y se comunican por HTTP. Además, en Kubernetes el cliente, el Pod y el Service son componentes de red distintos. No es una arquitectura de microservicios, pero sí es cliente-servidor distribuida. Si se agregaran más servicios o réplicas, la dimensión distribuida crecería.”

#### “¿Cómo garantiza que dos jugadores no jueguen al mismo tiempo?”

> “En el despliegue actual, Flask local usa `threaded=False` y Gunicorn usa un solo worker síncrono; las peticiones se serializan. Eso hace que el ‘leer turno, validar, cambiar turno’ no se intercale. Es una solución simple y suficiente para dos jugadores, pero no escala. Con varias réplicas usaría una transacción en base de datos y un bloqueo sobre la partida, o control de concurrencia optimista con un número de versión.”

#### “¿Qué pasa si se cae el Pod en medio de una partida?”

> “Kubernetes lo recrea porque el Deployment mantiene la réplica, pero el estado en memoria se pierde. Los jugadores tendrían que crear otra partida. Es la consecuencia directa de no tener persistencia. La solución es guardar partidas y usuarios en PostgreSQL; el Pod podría reiniciarse sin perder la partida.”

#### “¿Por qué no usó una imagen Docker propia?”

> “Porque el objetivo era demostrar el despliegue en Kubernetes sin depender de publicar una imagen. Usé una imagen oficial de Python y un initContainer que clona el repositorio público. Funciona, pero tiene costos: arranque lento, dependencia de GitHub/PyPI y código no inmutable. Si el requisito fuera una imagen propia, el Dockerfile está propuesto y el cambio en el Deployment sería reemplazar el initContainer por `image: mi-registro/picas:tag`.”

#### “¿Qué pasa si el profesor pide RPC en vez de REST?”

> “Mantendría el dominio y los servicios, y cambiaría la capa de entrada. Definiría un `.proto` con `JuegoService`, generaría el servidor y el cliente con `grpcio-tools`, y mapearía cada endpoint a un método. La lógica de `Game` no cambia. REST y RPC son formas de exponer el mismo caso de uso.”

---

## 17. Cierre de 30 segundos

> “En conclusión, Picas y Fijas es una aplicación cliente-servidor con reglas de juego bien separadas en el dominio, una API REST con autenticación por token y un despliegue funcional en Kubernetes. El flujo completo está probado: dos jugadores crean, se unen, juegan por turnos y terminan con cuatro fijas. La limitación principal es que el estado vive en memoria, y por eso el despliegue usa una réplica y un worker. La siguiente etapa es persistencia con PostgreSQL, pruebas automatizadas e imagen Docker propia. Con eso el proyecto pasaría de una demo sólida a una aplicación lista para producción.”

**Si te queda tiempo, agrega:** “Lo que más aprendí fue a diagnosticar fallos de Kubernetes y a separar la lógica del juego de la capa HTTP; eso hace que el proyecto sea fácil de explicar y de extender.”

---

## 18. Referencia rápida

### 18.1 Endpoints

| Método | Ruta | Auth | Qué hace |
| --- | --- | --- | --- |
| `GET` | `/` | No | Página HTML |
| `POST` | `/login` | No | Token firmado |
| `POST` | `/juego` | Bearer | Crear partida |
| `PUT` | `/juego/{id}` | Bearer | Unirse |
| `POST` | `/juego/{id}/jugar` | Bearer | Jugar intento |
| `GET` | `/juego/{id}` | Bearer | Ver partida (participantes) |
| `GET` | `/juego` | Bearer | Listar resumen |

### 18.2 Códigos

| Código | Uso en el proyecto |
| --- | --- |
| `200` | Login, unirse, jugar, consultar, listar |
| `201` | Crear partida |
| `400` | Número inválido, transición inválida, username no coincide |
| `401` | Sin token, token inválido o vencido |
| `403` | No participa o no es su turno |
| `404` | Partida inexistente, ruta inexistente |
| `405` | Método no permitido |
| `415` | `Content-Type` incorrecto |
| `500` | Error no controlado (HTML por defecto) |

### 18.3 Archivos clave

| Archivo | Para qué |
| --- | --- |
| `app/__init__.py` | Composition root, errores |
| `app/domain/game.py` | Reglas, picas/fijas, validación |
| `app/services/game_service.py` | Casos de uso, IDs |
| `app/services/auth_service.py` | Token firmado |
| `app/routes/game_routes.py` | Endpoints `/juego` |
| `app/routes/auth_routes.py` | `/login` |
| `app/routes/decorators.py` | `require_auth` |
| `app/repositories/*.py` | Contratos y memoria |
| `app/templates/index.html` | Frontend y polling |
| `killercoda/deployment.yaml` | Deployment |
| `killercoda/service.yaml` | Service |
| `killercoda/namespace.yaml` | Namespace |
| `README.md` | Contrato y ejecución |

### 18.4 Comandos

```bash
# Local
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m run
# Windows: .\.venv\Scripts\python.exe -m run

# Docker (propuesto)
docker build -t picas-y-fijas:1.0 .
docker run --rm -p 8080:5000 -e PICAS_SECRET_KEY=clave-segura picas-y-fijas:1.0

# Kubernetes
kubectl apply -f killercoda/namespace.yaml
kubectl -n picas-y-fijas create secret generic picas-auth \
  --from-literal=signing-key="$(openssl rand -hex 32)"
kubectl apply -f killercoda/deployment.yaml
kubectl apply -f killercoda/service.yaml
kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=300s
kubectl -n picas-y-fijas port-forward service/picas-y-fijas --address 0.0.0.0 8080:80

# Diagnóstico
kubectl -n picas-y-fijas get all
kubectl -n picas-y-fijas get pods -o wide
kubectl -n picas-y-fijas get endpoints
kubectl -n picas-y-fijas describe pod POD
kubectl -n picas-y-fijas logs POD -c web
kubectl -n picas-y-fijas logs POD -c web --previous
kubectl -n picas-y-fijas get events --sort-by=.metadata.creationTimestamp
```

### 18.5 Números y datos para recordar

| Dato | Valor |
| --- | --- |
| Dígitos del número secreto | 4, distintos |
| Dígitos del ID | 6, distintos, sin cero inicial |
| Combinaciones de ID | 136.080 |
| Vigencia del token | 3600 s (1 hora) |
| Polling | 2000 ms (2 s) |
| Réplicas | 1 |
| Workers de Gunicorn | 1 |
| Puerto local | 5000 |
| Puerto del Service | 80 |
| Puerto del contenedor | 5000 (nombre `http`) |
| Namespace | `picas-y-fijas` |
| Secret | `picas-auth`, clave `signing-key` |
| Imagen web | `python:3.12-slim` |
| Imagen init | `alpine/git:latest` |
| Commit defendido | `e9f59b2` |

### 18.6 Frases para cerrar una respuesta

- “Esa decisión está en `...` y la alternativa sería `...`.”
- “Lo mantuve simple por el alcance, pero el punto de extensión es `...`.”
- “La limitación es `...`; la solución sería `...`.”
- “No lo implementé, pero sé cómo se haría: `...`.”
- “El dominio no depende de Flask; por eso se puede probar y cambiar la entrada.”

### 18.7 Qué evitar decir

| Evita | Mejor di |
| --- | --- |
| “No sé.” | “No lo implementé; la solución sería …” |
| “Es que Flask es mejor.” | “Elegí Flask por simplicidad y por el alcance; Express también sería válido.” |
| “Kubernetes no lo entiendo.” | “El despliegue usa estos objetos; el que más me costó fue el initContainer/Secret.” |
| “Los tests están en el repo.” | “Hice 57 comprobaciones y pruebas manuales; la suite versionada es una mejora pendiente.” |
| “El token es seguro.” | “Está firmado, no cifrado; para producción falta HTTPS y revocación.” |
| “Escala con réplicas.” | “Hoy no escala horizontalmente por el estado en memoria; necesitaría base de datos.” |
| “REST es mejor que RPC.” | “REST encaja mejor con el navegador; RPC/gRPC encaja mejor con comunicación interna.” |

### 18.8 Checklist final antes de sustentar

- [ ] Puedo explicar el flujo completo en 60 segundos.
- [ ] Sé dibujar las cuatro capas y nombrar un archivo de cada una.
- [ ] Sé explicar picas/fijas con un ejemplo.
- [ ] Sé explicar la generación del ID y las 136.080 combinaciones.
- [ ] Sé explicar por qué el número es string.
- [ ] Sé explicar 401 vs 403 y 404 vs 405.
- [ ] Sé explicar el token firmado, su vigencia y sus límites.
- [ ] Sé explicar por qué hay una réplica y un worker.
- [ ] Sé explicar qué pasa al reiniciar el servidor.
- [ ] Sé explicar el Deployment, el Service, el initContainer y el emptyDir.
- [ ] Sé diagnosticar `CrashLoopBackOff`, `CreateContainerConfigError` y Service sin endpoints.
- [ ] Sé explicar por qué no hay Dockerfile y cómo se haría.
- [ ] Sé explicar REST vs RPC y cómo sería gRPC.
- [ ] Tengo el plan B de la demo si Kubernetes falla.
- [ ] Tengo dos pestañas y los números de prueba listos.
- [ ] No voy a mostrar secretos reales en pantalla.

### 18.9 Guion de bolsillo (2 minutos)

1. “Picas y Fijas: dos jugadores, cuatro dígitos distintos, picas y fijas; gana quien logra cuatro fijas.”
2. “Frontend HTML/JS, API REST en Flask y dominio separado de las rutas.”
3. “Cuatro capas: rutas → servicios → dominio → repositorios; `create_app` conecta todo.”
4. “Autenticación con token firmado de una hora; el username sale del token, no del body.”
5. “El secreto nunca se devuelve: `to_dict()` excluye `_secrets`.”
6. “IDs de seis dígitos distintos, sin cero inicial: 136.080 combinaciones y reintento ante colisión.”
7. “Kubernetes: namespace, Secret, Deployment con `initContainer` y Service `ClusterIP`.”
8. “Una réplica y un worker porque el estado vive en memoria.”
9. “La limitación principal es la falta de persistencia; la siguiente mejora es PostgreSQL, tests e imagen propia.”

**Si te preguntan “¿y por qué no…?”:** responde con la decisión, el costo y la alternativa. Ejemplo: “Usé estado en memoria para evitar dependencias; el costo es que no escala ni persiste; la alternativa es PostgreSQL con transacciones”.

---

> **Documento vivo:** si cambias el código (por ejemplo, agregas persistencia o un Dockerfile), actualiza esta guía y el README. La defensa debe coincidir con el commit que muestras.
