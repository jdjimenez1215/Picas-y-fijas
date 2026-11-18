# Apunte de bolsillo — Parcial de API, Docker, RPC y Kubernetes

> **Proyecto de referencia:** Picas y Fijas (Flask + REST + Kubernetes).
> **Material de clase:** `server.js` (Express), `Dockerfile` (Node) y `k8s.docx` (Deployment, Service, endpoints y temas).
>
> **Cómo usar este apunte:** no está ordenado para estudiar, sino para **resolver ejercicios**. Busca la frase del profesor en la tabla de abajo y ve directo a esa sección.

## Índice por tipo de ejercicio

| Si el profesor dice… | Ve a… |
| --- | --- |
| “Complete el servidor Express / agregue un endpoint” | [§1.3](#13-express-plantilla-completa) |
| “Complete el servidor Flask / API REST” | [§1.4](#14-flask-plantilla-equivalente) |
| “¿Por qué no llega el body / por qué 415 / por qué 401?” | [§1.8](#18-errores-típicos-en-api) y §5.5 |
| “Escriba o corrija el Dockerfile” | [§2.2](#22-dockerfile-de-clase-node) y [§2.3](#23-versión-mejorada-para-node) |
| “¿Por qué el contenedor no arranca o no abre el puerto?” | [§2.8](#28-errores-típicos-en-docker) |
| “JSON-RPC / gRPC / proto / complete el RPC” | [§3](#3-rpc) |
| “Escriba el Deployment y el Service” | [§4.2](#42-deployment-de-clase) y [§4.3](#43-service-de-clase) |
| “El Pod está en CrashLoopBackOff / Pending / no responde” | §4.8 |
| “¿Por qué falla este YAML / este código?” | [§5](#5-simulacro-integrador) |
| “¿Qué es REST / RPC / un Pod / una imagen?” | [§6](#6-teoría-mínima-para-responder) |

> **Ruta corta si solo puedes llevar dos páginas:** imprime §0 (códigos y métodos), §1.3 (plantilla Express), §2.2 (Dockerfile de clase), §3.2 (JSON-RPC), §4.2–§4.3 (Deployment y Service), §4.8 (diagnóstico) y §7 (checklist). El resto es material de consulta para completar ejercicios.

## Plan de repaso de 90 minutos

| Bloque | Minutos | Qué hacer |
| --- | --- | --- |
| 1 | 15 | §0 y §1.1–§1.2: códigos, métodos y headers. Recita la regla `400/401/403/404`. |
| 2 | 25 | §1.3 y §1.4: escribe la plantilla Express de memoria y compárala. |
| 3 | 20 | §2: Dockerfile de clase, errores y mapeo `-p`. |
| 4 | 15 | §3: JSON-RPC y `.proto`. |
| 5 | 15 | §4: Deployment/Service y diagnóstico. |
| 6 | 10 | §8: autoevaluación. Si fallas tres o más, vuelve al bloque correspondiente. |

---

## 0. Chuleta de 60 segundos

### 0.1 Códigos HTTP que más se usan

| Código | Cuándo usarlo | Ejemplo |
| --- | --- | --- |
| `200 OK` | Éxito con body | `GET /juego`, `POST /login` |
| `201 Created` | Se creó un recurso | `POST /juego` + `Location` |
| `204 No Content` | Éxito sin body | `DELETE` |
| `400 Bad Request` | Datos inválidos, JSON malo, transición inválida | Número con dígitos repetidos |
| `401 Unauthorized` | No hay token o es inválido/vencido | Falta `Authorization` |
| `403 Forbidden` | Autenticado pero sin permiso | No es tu turno |
| `404 Not Found` | No existe el recurso o la ruta | Partida inexistente |
| `405 Method Not Allowed` | Método HTTP equivocado | `DELETE /juego` |
| `409 Conflict` | Conflicto con el estado | Unirse a partida llena |
| `415 Unsupported Media Type` | `Content-Type` incorrecto | Enviar texto sin `application/json` |
| `422 Unprocessable Entity` | Sintaxis válida, semántica inválida | Validación de campos |
| `429 Too Many Requests` | Rate limit | Demasiados intentos |
| `500 Internal Server Error` | Excepción no controlada | Bug en el servidor |
| `502/503/504` | Fallo de proxy / servicio no disponible / timeout | Ingress sin endpoints |

**Regla de oro:** el código debe decir **quién** falló y **por qué**. Si el cliente no se identificó → `401`; si se identificó pero no puede → `403`; si mandó mal los datos → `400`; si el recurso no existe → `404`.

### 0.2 Métodos HTTP

| Método | Sirve para | ¿Seguro? | ¿Idempotente? |
| --- | --- | --- | --- |
| `GET` | Leer | Sí | Sí |
| `POST` | Crear o ejecutar una acción | No | No |
| `PUT` | Reemplazar/actualizar un recurso | No | Sí |
| `PATCH` | Actualizar parcialmente | No | No necesariamente |
| `DELETE` | Borrar | No | Sí |
| `HEAD` | Como GET, sin body | Sí | Sí |
| `OPTIONS` | Capacidades / CORS | Sí | Sí |

- **Seguro:** no cambia el estado del servidor.
- **Idempotente:** repetir la misma petición deja el mismo estado final.
- `POST /juego` no es idempotente: dos llamadas crean dos partidas.
- `POST /juego/{id}/jugar` no es idempotente: cada intento cuenta y cambia el turno.

### 0.3 Headers que hay que recordar

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer TOKEN
Location: /juego/482913
```

- Sin `Content-Type: application/json`, Flask puede devolver `415` y Express no parsea el body.
- `Authorization: Bearer TOKEN` es el formato que usa el proyecto.
- `Location` se devuelve con `201` para indicar dónde quedó el recurso creado.

### 0.4 Docker, Kubernetes y RPC en una línea

| Tema | Idea mínima |
| --- | --- |
| **Docker** | Imagen = plantilla; contenedor = instancia. `docker build` → `docker run -p host:contenedor`. |
| **Kubernetes** | Declaras el estado deseado en YAML; el clúster crea Pods, los reinicia y los expone con un Service. |
| **RPC** | Llamar una función remota como si fuera local; JSON-RPC usa JSON, gRPC usa protobuf + HTTP/2. |
| **REST** | Recursos + HTTP + JSON + stateless; se modela con sustantivos (`/juego`). |

---

## 1. API y REST

### 1.1 Anatomía de una petición y una respuesta

```http
POST /juego HTTP/1.1
Host: localhost:5000
Authorization: Bearer eyJ1c2VybmFtZSI6ImFuYSJ9...
Content-Type: application/json

{"number":"4271"}
```

```http
HTTP/1.1 201 CREATED
Content-Type: application/json
Location: /juego/482913

{"id":"482913","creator":"ana","players":["ana"],"status":"waiting","turn":null,"attempts":[],"winner":null}
```

Partes de una petición:

- **Método**: `GET`, `POST`, `PUT`, `DELETE`…
- **Ruta**: `/juego/482913`.
- **Headers**: metadatos (`Content-Type`, `Authorization`).
- **Query params**: `/juego?limit=10`.
- **Body**: datos (normalmente JSON).

Partes de una respuesta:

- **Código de estado**: `200`, `201`, `400`, `401`, `403`, `404`, `500`…
- **Headers**: `Content-Type`, `Location`…
- **Body**: JSON, HTML o vacío.

### 1.2 Reglas REST que siempre se preguntan

1. **Cliente-servidor:** el front no conoce la base de datos; solo llama la API.
2. **Stateless:** cada petición trae todo lo necesario. El proyecto manda el token en cada request; el servidor no guarda sesión.
3. **Recursos con sustantivos:** `/juego`, `/juego/{id}`; no `/crearJuego`.
4. **HTTP como interfaz uniforme:** el método expresa la intención.
5. **Representaciones:** el recurso se envía como JSON.
6. **Cacheable:** se puede indicar con headers; no es obligatorio.
7. **Sistema en capas:** puede haber proxy, balanceador o Ingress.

**REST no es un protocolo ni una librería**: es un estilo arquitectónico. Por eso el proyecto puede ser REST aunque use Flask y no Express.

### 1.3 Express: plantilla completa

Esta plantilla es una API de Picas y Fijas **mínima pero funcional**. Sirve para un ejercicio de “complete el servidor” o “agregue autenticación”.

```js
const express = require('express');
const { randomUUID } = require('crypto');

const app = express();
const PORT = process.env.PORT || 3000;

// ✔ Sin esta línea, req.body es undefined
app.use(express.json());

const tokens = new Map();   // token -> username
const games = new Map();    // id -> partida

// ---------- Utilidades ----------
const publicGame = ({ secrets, ...game }) => game;

const validNumber = (n) =>
  typeof n === 'string' &&
  /^[0-9]{4}$/.test(n) &&
  new Set(n).size === 4;

const auth = (req, res, next) => {
  const header = req.headers.authorization || '';
  if (!header.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Falta el header Authorization: Bearer <token>' });
  }
  const username = tokens.get(header.slice(7));
  if (!username) {
    return res.status(401).json({ error: 'Token inválido' });
  }
  req.username = username;
  next();
};

// ---------- Rutas ----------
app.get('/', (req, res) => {
  res.send('Picas y Fijas API');
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.post('/login', (req, res) => {
  const { username } = req.body || {};
  if (!username || typeof username !== 'string') {
    return res.status(400).json({ error: 'username es obligatorio' });
  }
  const token = randomUUID();
  tokens.set(token, username);
  res.json({ token });
});

app.post('/juego', auth, (req, res) => {
  const { number } = req.body || {};
  if (!validNumber(number)) {
    return res.status(400).json({ error: 'Número inválido: 4 dígitos distintos' });
  }
  let id;
  do {
    id = String(Math.floor(100000 + Math.random() * 900000));
  } while (games.has(id));

  const game = {
    id,
    creator: req.username,
    players: [req.username],
    secrets: { [req.username]: number },
    status: 'waiting',
    turn: null,
    attempts: [],
    winner: null,
  };
  games.set(id, game);
  res.status(201).location(`/juego/${id}`).json(publicGame(game));
});

app.get('/juego', auth, (req, res) => {
  res.json([...games.values()].map(publicGame));
});

app.get('/juego/:id', auth, (req, res) => {
  const game = games.get(req.params.id);
  if (!game) return res.status(404).json({ error: 'Partida no encontrada' });
  if (!game.players.includes(req.username)) {
    return res.status(403).json({ error: 'No participas en esta partida' });
  }
  res.json(publicGame(game));
});

app.put('/juego/:id', auth, (req, res) => {
  const game = games.get(req.params.id);
  if (!game) return res.status(404).json({ error: 'Partida no encontrada' });
  if (game.status === 'finished') {
    return res.status(400).json({ error: 'No puedes unirte: la partida ya terminó' });
  }
  if (game.players.includes(req.username)) {
    return res.status(400).json({ error: 'Ya estás en la partida' });
  }
  if (game.status !== 'waiting') {
    return res.status(400).json({ error: 'La partida ya tiene dos jugadores' });
  }
  const { username, number } = req.body || {};
  if (username !== req.username) {
    return res.status(400).json({ error: 'username debe coincidir con el token' });
  }
  if (!validNumber(number)) {
    return res.status(400).json({ error: 'Número inválido: 4 dígitos distintos' });
  }
  game.players.push(req.username);
  game.secrets[req.username] = number;
  game.status = 'in_progress';
  game.turn = game.players[Math.floor(Math.random() * 2)];
  res.json(publicGame(game));
});

app.post('/juego/:id/jugar', auth, (req, res) => {
  const game = games.get(req.params.id);
  if (!game) return res.status(404).json({ error: 'Partida no encontrada' });
  if (!game.players.includes(req.username)) {
    return res.status(403).json({ error: 'No participas en esta partida' });
  }
  if (game.status !== 'in_progress') {
    return res.status(400).json({ error: 'La partida no está en juego' });
  }
  if (game.turn !== req.username) {
    return res.status(403).json({ error: 'No es tu turno' });
  }
  const { number } = req.body || {};
  if (!validNumber(number)) {
    return res.status(400).json({ error: 'Número inválido: 4 dígitos distintos' });
  }

  const opponent = game.players.find((p) => p !== req.username);
  const secret = game.secrets[opponent];
  const fijas = [...number].filter((d, i) => d === secret[i]).length;
  const picas = [...number].filter((d) => secret.includes(d)).length - fijas;

  const result = { player: req.username, guess: number, fijas, picas };
  game.attempts.push(result);

  if (fijas === 4) {
    game.status = 'finished';
    game.winner = req.username;
    game.turn = null;
  } else {
    game.turn = opponent;
  }
  res.json(result);
});

// ---------- 404 y errores ----------
app.use((req, res) => {
  res.status(404).json({ error: 'Ruta no encontrada' });
});

app.use((err, req, res, next) => {
  if (err.type === 'entity.parse.failed') {
    return res.status(400).json({ error: 'JSON inválido' });
  }
  console.error(err);
  res.status(500).json({ error: 'Error interno' });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Servidor en http://localhost:${PORT}`);
});
```

**Simplificación:** esta plantilla usa un ID aleatorio de seis dígitos. El proyecto real exige además que los seis dígitos sean distintos y verifica colisiones antes de guardar; aquí se omitió para no alargar el ejemplo.

**Cosas que el profesor suele revisar en este código:**

| Punto | ¿Está? |
| --- | --- |
| `app.use(express.json())` | ✔ |
| `process.env.PORT` | ✔ |
| `res.status(...)` correcto | ✔ |
| `Authorization: Bearer` | ✔ |
| Validación de 4 dígitos distintos | ✔ |
| No devolver `secrets` | ✔ (`publicGame`) |
| `201` + `Location` al crear | ✔ |
| `404` y `500` en JSON | ✔ |
| `0.0.0.0` al escuchar | ✔ |

### 1.4 Flask: plantilla equivalente

El proyecto usa **app factory + blueprints + capas**. Para un ejercicio pequeño, esta versión condensada muestra lo esencial:

```python
import os
from functools import wraps

from flask import Flask, request, jsonify, g
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="auth")
games = {}


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify(error="Falta el header Authorization: Bearer <token>"), 401
        try:
            data = serializer.loads(header[7:], max_age=3600)
        except (BadSignature, SignatureExpired):
            return jsonify(error="Token inválido o expirado"), 401
        g.username = data["username"]
        return f(*args, **kwargs)
    return wrapper


@app.post("/login")
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data.get("username"):
        return jsonify(error="username es obligatorio"), 400
    token = serializer.dumps({"username": data["username"]})
    return jsonify(token=token)


@app.post("/juego")
@require_auth
def create_game():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="El cuerpo debe ser un objeto JSON"), 400
    number = data.get("number")
    if not isinstance(number, str) or len(number) != 4 or not number.isdigit() or len(set(number)) != 4:
        return jsonify(error="Número inválido: 4 dígitos distintos"), 400
    game_id = "482913"  # en el proyecto se genera y se verifica que no exista
    games[game_id] = {"id": game_id, "creator": g.username, "players": [g.username]}
    return jsonify(games[game_id]), 201, {"Location": f"/juego/{game_id}"}


@app.errorhandler(HTTPException)
def http_error(e):
    # 404, 405, 415, etc. en JSON, no en HTML
    return jsonify(error=e.name, description=e.description), e.code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=False)
```

**Diferencias clave Flask vs Express:**

| Flask | Express |
| --- | --- |
| `request.get_json()` | `req.body` + `express.json()` |
| `jsonify(...)` | `res.json(...)` |
| `return body, status, headers` | `res.status(...).json(...)` |
| `Blueprint` | `express.Router()` |
| `@app.errorhandler` | `app.use((err, req, res, next) => ...)` |
| `g.username` | `req.username` |

### 1.5 cURL para probar cualquier endpoint

```bash
# Login
curl -i -X POST http://localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"ana"}'

# Guardar el token en una variable (Linux/macOS)
TOKEN=$(curl -s -X POST http://localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"ana"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

# Crear partida
curl -i -X POST http://localhost:5000/juego \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"number":"4271"}'

# Unirse
curl -i -X PUT http://localhost:5000/juego/482913 \
  -H "Authorization: Bearer $TOKEN_LUIS" \
  -H 'Content-Type: application/json' \
  -d '{"username":"luis","number":"0123"}'

# Jugar
curl -i -X POST http://localhost:5000/juego/482913/jugar \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"number":"1234"}'
```

**Bandera por bandera:**

| Bandera | Para qué |
| --- | --- |
| `-i` | Muestra headers de respuesta |
| `-X POST` | Método HTTP |
| `-H` | Header |
| `-d` | Body |
| `-s` | Silencioso (sin barra de progreso) |
| `-v` | Verbose, para depurar conexión |
| `--fail` | Falla si el código es ≥ 400 |

### 1.6 Fórmula de picas y fijas

```python
fijas = sum(digito == secreto for digito, secreto in zip(intento, secreto))
picas = sum(digito in secreto for digito in intento) - fijas
```

```js
const fijas = [...intento].filter((d, i) => d === secreto[i]).length;
const picas = [...intento].filter((d) => secreto.includes(d)).length - fijas;
```

Ejemplo: secreto `4271`, intento `4172`.

- Posición 0: `4` = `4` → fija.
- Posición 1: `1` ≠ `2`, pero `1` está en `4271` → pica.
- Posición 2: `7` = `7` → fija.
- Posición 3: `2` ≠ `1`, pero `2` está en `4271` → pica.

Resultado: **2 fijas, 2 picas**.

> Los dígitos son distintos, así que no hay que preocuparse por contar dos veces el mismo dígito.

### 1.7 “¿Qué le falta?” — checklist de API

Si el ejercicio dice “complete la API”, revisa en este orden:

1. `app.use(express.json())` (Express) o `request.get_json()` (Flask).
2. `Content-Type: application/json` en el cliente.
3. Código de estado correcto (`201` al crear, `400` al validar, `401/403` al autorizar).
4. Validar tipos y reglas: `number` debe ser **string** de 4 dígitos distintos.
5. No devolver secretos ni contraseñas.
6. `Authorization: Bearer <token>` en rutas protegidas.
7. `404` para recurso inexistente y `405` para método incorrecto.
8. `Location` en la respuesta `201`.
9. `0.0.0.0` al escuchar dentro de Docker/Kubernetes.
10. Manejo de errores en JSON, no HTML.

### 1.8 Errores típicos en API

| Síntoma | Causa | Solución |
| --- | --- | --- |
| `req.body` es `undefined` | Falta `app.use(express.json())` | Agregar el middleware antes de las rutas |
| `415 Unsupported Media Type` | Falta `Content-Type: application/json` | Agregar el header |
| `400` por JSON | JSON mal formado o body no es objeto | Validar `typeof data === 'object'` |
| `401` siempre | No se manda `Authorization` o el token venció | Revisar header y relogin |
| `403` | El usuario existe pero no es su turno / no participa | Revisar lógica de permisos |
| `404` | ID inexistente o ruta mal escrita | Revisar URL |
| `405` | Método HTTP equivocado | Usar el método de la tabla |
| `500` | Excepción no controlada | Ver logs y reproducir |
| `0123` llega como `123` | Se envió como número, no como string | Enviar `"0123"` |
| CORS bloquea | Front en otro origen | Configurar CORS o mismo origen |
| `GET /juego` devuelve secretos | Se serializó el objeto completo | Excluir `secrets` en `to_dict`/`publicGame` |

### 1.9 Ejercicios resueltos de API

#### E1. Completar el `server.js` de clase para que acepte JSON y tenga login

**Enunciado:** el servidor solo tiene `/` y `/health`. Agregue `POST /login` que reciba `{"username":"ana"}` y devuelva `{"token":"..."}`. Si falta `username`, debe responder `400`.

**Respuesta:**

```js
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json()); // ← lo que faltaba

app.post('/login', (req, res) => {
  const { username } = req.body || {};
  if (!username) {
    return res.status(400).json({ error: 'username es obligatorio' });
  }
  res.json({ token: 'token-de-' + username });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Servidor en http://localhost:${PORT}`);
});
```

**Por qué:** sin `express.json()`, `req.body` no existe; sin `res.status(400)`, el error saldría como `200`.

#### E2. ¿Por qué `req.body` es `undefined`?

**Respuesta:** porque falta el middleware `app.use(express.json())` o el cliente no envió `Content-Type: application/json`. Express no parsea el body automáticamente.

#### E3. El cliente recibe `415`

**Respuesta:** el `Content-Type` no es `application/json`. En Flask, `request.get_json()` rechaza el body; en Express, el middleware no lo parsea. Se corrige con el header correcto.

#### E4. ¿`401` o `403`?

- Sin header `Authorization` → **401**.
- Token vencido → **401**.
- Token válido, pero el jugador no pertenece a la partida → **403**.
- Token válido, pero no es su turno → **403**.

#### E5. Devolver `201` con `Location`

```js
res.status(201)
   .location(`/juego/${game.id}`)
   .json(publicGame(game));
```

En Flask:

```python
return jsonify(game.to_dict()), 201, {"Location": f"/juego/{game.id}"}
```

#### E6. Validar cuatro dígitos distintos

```js
const validNumber = (n) =>
  typeof n === 'string' && /^[0-9]{4}$/.test(n) && new Set(n).size === 4;
```

```python
def valid_number(n):
    return isinstance(n, str) and len(n) == 4 and n.isdigit() and len(set(n)) == 4
```

**Trampa:** `Number("0123")` es `123`; por eso el número viaja como **string**.

#### E7. ¿Por qué no se debe devolver el número secreto?

Porque cualquier jugador podría leerlo con `GET /juego/{id}` y hacer trampa. En el proyecto, `Game.to_dict()` no incluye `_secrets`; devuelve `id`, `creator`, `players`, `status`, `turn`, `attempts` y `winner`, pero nunca los números secretos.

---

## 2. Docker

### 2.1 Conceptos que siempre caen

| Concepto | Definición |
| --- | --- |
| **Imagen** | Plantilla de solo lectura con la app y sus dependencias. |
| **Contenedor** | Instancia en ejecución de una imagen; tiene su propio filesystem, red y procesos. |
| **Dockerfile** | Receta para construir una imagen. |
| **Registro** | Repositorio de imágenes (Docker Hub, GHCR, ECR). |
| **Volumen** | Almacenamiento persistente fuera del contenedor. |
| **Red** | Los contenedores se comunican por nombre de servicio (Compose) o por IP. |
| **Capa** | Cada instrucción del Dockerfile genera una capa cacheable. |

**Contenedor vs máquina virtual:**

| VM | Contenedor |
| --- | --- |
| Incluye un SO completo | Comparte el kernel del host |
| Más pesada | Más liviana |
| Aislamiento más fuerte | Aislamiento por namespaces/cgroups |
| Arranque lento | Arranque rápido |

### 2.2 Dockerfile de clase (Node)

```dockerfile
# Use official lightweight Node.js image
FROM node:26-alpine3.22

# Set working directory
WORKDIR /app

# Generate package.json and install express in one step
# RUN curl -fsSL https://get.pnpm.io/install.sh | sh -

RUN npm init -y \
 && npm install express --omit=dev \
 && npm pkg set scripts.start="node server.js"

# Copy rest of the app (server.js, etc.)
COPY . .

# Expose port
EXPOSE 3000

# Run as non-root user
USER node

# Start the app
CMD ["npm", "start"]
```

**Qué hace cada instrucción:**

| Instrucción | Efecto |
| --- | --- |
| `FROM` | Imagen base. |
| `WORKDIR` | Directorio de trabajo; se crea si no existe. |
| `RUN` | Ejecuta durante el **build** y crea una capa. |
| `COPY` | Copia archivos del contexto de build. |
| `EXPOSE` | **Documenta** el puerto; no lo publica. |
| `USER` | Corre como usuario no root. |
| `CMD` | Comando por defecto; se puede sobrescribir. |

**Críticas útiles (si preguntan “¿qué mejorarías?”):**

- `npm init -y` + `npm install` en el build funciona, pero no aprovecha bien la caché: cualquier cambio en el código invalida la instalación.
- `COPY . .` puede copiar `node_modules`, `.git` y basura si no hay `.dockerignore`.
- `EXPOSE 3000` no abre el puerto; hay que usar `-p 8080:3000`.
- `CMD ["npm","start"]` está bien (forma exec), pero `npm` como PID 1 no siempre propaga señales; para producción conviene `CMD ["node","server.js"]`.
- Fijar `node:26-alpine3.22` es válido, pero en producción conviene una versión LTS y, si se puede, un digest.

### 2.3 Versión mejorada para Node

Si el proyecto tiene `package.json` y `package-lock.json` versionados:

```dockerfile
FROM node:22-alpine

WORKDIR /app

# 1) Dependencias primero: si el código cambia, esta capa se reutiliza
COPY package*.json ./
RUN npm ci --omit=dev

# 2) Código después
COPY . .

# 3) Usuario no root
USER node

EXPOSE 3000
CMD ["node", "server.js"]
```

`.dockerignore`:

```text
node_modules
npm-debug.log
.git
.gitignore
Dockerfile
README.md
```

**Diferencia clave:** `COPY package*.json` antes de `COPY . .` permite cachear `npm ci`; si solo cambia `server.js`, no se reinstala todo.

### 2.4 Dockerfile para el proyecto Flask

El proyecto **no incluye Dockerfile**: en Kubernetes usa `python:3.12-slim` y instala dependencias al arrancar. Si el profesor pide dockerizarlo, esta es la respuesta:

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

**Por qué un solo worker:** las partidas están en memoria. Dos workers tendrían dos diccionarios distintos y los jugadores verían estados diferentes. Para escalar haría falta una base de datos o Redis.

### 2.5 Comandos de Docker

```bash
# Construir
docker build -t mi-api:1.0 .

# Ejecutar en primer plano, publicando 8080 del host al 3000 del contenedor
docker run --rm -p 8080:3000 --name mi-api mi-api:1.0

# En segundo plano
docker run -d -p 8080:3000 --name mi-api mi-api:1.0

# Variables de entorno
docker run --rm -p 8080:3000 -e PORT=3000 mi-api:1.0

# Ver contenedores (incluye detenidos)
docker ps
docker ps -a

# Logs
docker logs -f mi-api

# Entrar al contenedor
docker exec -it mi-api sh

# Detener y eliminar
docker stop mi-api
docker rm mi-api

# Imágenes
docker images
docker rmi mi-api:1.0
```

**Mapeo de puertos:** `-p HOST:CONTENEDOR`. `-p 8080:3000` significa “abre el 8080 en mi máquina y envíalo al 3000 del contenedor”. El `EXPOSE 3000` del Dockerfile no basta.

### 2.6 Docker Compose

```yaml
services:
  api:
    build: .
    ports:
      - "8080:3000"
    environment:
      PORT: "3000"
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3000/health"]
      interval: 10s
      timeout: 3s
      retries: 3
```

```bash
docker compose up -d --build
docker compose logs -f
docker compose down
```

### 2.7 “¿Qué le falta?” — checklist de Dockerfile

1. `FROM` con una imagen base válida.
2. `WORKDIR` definido.
3. Dependencias copiadas e instaladas **antes** del código.
4. `COPY` de todo el código.
5. `EXPOSE` del puerto correcto (documental).
6. `USER` no root.
7. `CMD` en forma exec (`["node","server.js"]`).
8. `.dockerignore`.
9. Variables de entorno para configuración (`PORT`, `PICAS_SECRET_KEY`).
10. La app escuchando en `0.0.0.0`, no en `127.0.0.1`.

### 2.8 Errores típicos en Docker

| Error / síntoma | Causa | Solución |
| --- | --- | --- |
| `COPY failed: file not found` | El archivo no está en el contexto o lo excluyó `.dockerignore` | Revisar ruta y contexto |
| `port is already allocated` | El puerto del host está ocupado | Cambiar `-p` o liberar el puerto |
| `exec format error` | Imagen de otra arquitectura | Usar `--platform` o build multiplataforma |
| El contenedor sale inmediatamente | El comando principal falló o terminó | `docker logs`, revisar `CMD` |
| `permission denied` | Usuario sin permisos | Ajustar `USER` y permisos |
| No se accede desde el host | La app escucha en `127.0.0.1` dentro del contenedor | Escuchar en `0.0.0.0` |
| `Cannot find module` | Faltó copiar dependencias o `node_modules` | `npm ci` en el Dockerfile |
| Cambios no se reflejan | Caché de build | `docker build --no-cache` |
| Imagen enorme | Se copió todo el contexto | `.dockerignore`, multi-stage |
| `docker: command not found` | Docker no está instalado o no está en PATH | Instalar/abrir Docker |

### 2.9 Ejercicios resueltos de Docker

#### E1. Corregir este Dockerfile

**Enunciado:** el siguiente Dockerfile falla o es inseguro. Encuentre los problemas.

```dockerfile
FROM node:latest
WORKDIR /app
COPY . .
RUN npm install
EXPOSE 3000
CMD npm start
```

**Problemas:**

1. `node:latest` es mutable; mejor una versión fija.
2. `COPY . .` antes de instalar copia `node_modules` y rompe la caché.
3. `npm install` instala dependencias de desarrollo; usar `npm ci --omit=dev`.
4. No hay `USER` no root.
5. `CMD npm start` es forma shell; mejor `CMD ["node","server.js"]`.
6. Falta `.dockerignore`.

**Corrección:**

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

> Si no hay `package-lock.json`, `npm ci` falla; en ese caso usa `RUN npm install --omit=dev` o genera el lock antes de construir.

#### E2. El contenedor arranca y muere

**Respuesta:** revisar `docker logs mi-api`. Causas típicas: el comando `CMD` no existe, falta un archivo, la app lanza una excepción al iniciar o el proceso termina porque no queda en primer plano. `docker ps -a` muestra el código de salida.

#### E3. El contenedor corre pero `localhost:8080` no responde

**Respuesta:** probablemente la app escucha en `127.0.0.1` dentro del contenedor. Debe escuchar en `0.0.0.0`. También puede faltar `-p 8080:3000` o el puerto interno puede ser distinto.

#### E4. `COPY failed: file not found`

**Respuesta:** el archivo no está en el contexto de build (la carpeta que se pasa a `docker build`), o `.dockerignore` lo excluyó. Recordar que `COPY` no puede acceder a rutas fuera del contexto (`../`).

#### E5. Construir y ejecutar el proyecto Flask

```bash
docker build -t picas:1.0 .
docker run --rm -p 8080:5000 -e PICAS_SECRET_KEY=clave-segura picas:1.0
# Abrir http://localhost:8080
```

---

## 3. RPC

### 3.1 RPC vs REST

| Aspecto | REST | RPC |
| --- | --- | --- |
| Modelo | Recursos | Acciones/funciones |
| Interfaz | URL + método HTTP | IDL + stubs |
| Formato | JSON/XML | JSON, protobuf, binario |
| Acoplamiento | Más débil | Más fuerte (contrato) |
| Rendimiento | Bueno | Muy bueno con binario/HTTP2 |
| Streaming | Limitado | gRPC tiene 4 modos |
| Navegador | Nativo | gRPC-Web o JSON-RPC |
| Ejemplo | `POST /juego` | `JuegoService.CrearJuego(...)` |

**No hay uno mejor siempre.** REST es ideal para APIs públicas y recursos; RPC/gRPC para comunicación interna, contratos fuertes y alto rendimiento.

### 3.2 JSON-RPC 2.0: servidor completo

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

def sumar(params):
    return params["a"] + params["b"]

def crear_juego(params):
    if not params.get("numero"):
        raise ValueError("numero es obligatorio")
    return {"id": "482913", "estado": "waiting"}

methods = {
    "sumar": sumar,
    "crearJuego": crear_juego,
}

@app.post("/rpc")
def rpc():
    req = request.get_json(silent=True)
    if not isinstance(req, dict):
        req = {}
    rid = req.get("id")

    if req.get("jsonrpc") != "2.0" or "method" not in req:
        return jsonify(jsonrpc="2.0", error={"code": -32600, "message": "Invalid Request"}, id=rid), 400

    method = req["method"]
    if method not in methods:
        return jsonify(jsonrpc="2.0", error={"code": -32601, "message": "Method not found"}, id=rid), 404

    try:
        result = methods[method](req.get("params", {}))
        return jsonify(jsonrpc="2.0", result=result, id=rid)
    except Exception as e:
        return jsonify(jsonrpc="2.0", error={"code": -32602, "message": str(e)}, id=rid), 400
```

**Petición:**

```json
{"jsonrpc":"2.0","method":"sumar","params":{"a":2,"b":3},"id":1}
```

**Respuesta:**

```json
{"jsonrpc":"2.0","result":5,"id":1}
```

**Error:**

```json
{"jsonrpc":"2.0","error":{"code":-32601,"message":"Method not found"},"id":1}
```

**cURL:**

```bash
curl -i -X POST http://localhost:5000/rpc \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"sumar","params":{"a":2,"b":3},"id":1}'
```

### 3.3 gRPC: proto, servidor y cliente

**Contrato `picas.proto`:**

```proto
syntax = "proto3";

package picas;

service JuegoService {
  rpc CrearJuego (CrearJuegoRequest) returns (JuegoReply);
  rpc Jugar (JugarRequest) returns (JugadaReply);
}

message CrearJuegoRequest {
  string jugador = 1;
  string numero = 2;
}

message JugarRequest {
  string id = 1;
  string jugador = 2;
  string numero = 3;
}

message JuegoReply {
  string id = 1;
  string creador = 2;
  repeated string jugadores = 3;
  string estado = 4;
  string turno = 5;
  string ganador = 6;
}

message JugadaReply {
  string jugador = 1;
  string intento = 2;
  int32 fijas = 3;
  int32 picas = 4;
}
```

**Generar código Python:**

```bash
pip install grpcio grpcio-tools
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. picas.proto
```

**Servidor:**

```python
from concurrent import futures
import grpc
import picas_pb2
import picas_pb2_grpc

class JuegoServicer(picas_pb2_grpc.JuegoServiceServicer):
    def CrearJuego(self, request, context):
        if len(request.numero) != 4:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Número inválido")
        return picas_pb2.JuegoReply(
            id="482913",
            creador=request.jugador,
            jugadores=[request.jugador],
            estado="waiting",
        )

server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
picas_pb2_grpc.add_JuegoServiceServicer_to_server(JuegoServicer(), server)
server.add_insecure_port("[::]:50051")
server.start()
server.wait_for_termination()
```

**Cliente:**

```python
import grpc
import picas_pb2
import picas_pb2_grpc

with grpc.insecure_channel("localhost:50051") as channel:
    stub = picas_pb2_grpc.JuegoServiceStub(channel)
    reply = stub.CrearJuego(
        picas_pb2.CrearJuegoRequest(jugador="ana", numero="4271"),
        timeout=2,
    )
    print(reply.id, reply.estado)
```

**Modos de streaming:**

- **Unary:** una petición, una respuesta.
- **Server streaming:** una petición, muchas respuestas.
- **Client streaming:** muchas peticiones, una respuesta.
- **Bidirectional:** muchas en ambos sentidos.

### 3.4 Códigos de error

**JSON-RPC:**

| Código | Significado |
| --- | --- |
| `-32700` | Parse error (JSON mal formado) |
| `-32600` | Invalid Request |
| `-32601` | Method not found |
| `-32602` | Invalid params |
| `-32603` | Internal error |

**gRPC:**

| Código | Significado |
| --- | --- |
| `OK` | Éxito |
| `INVALID_ARGUMENT` | Argumentos inválidos |
| `NOT_FOUND` | No existe |
| `PERMISSION_DENIED` | Sin permiso |
| `UNAUTHENTICATED` | Falta autenticación |
| `DEADLINE_EXCEEDED` | Se acabó el tiempo |
| `UNAVAILABLE` | Servidor no disponible |
| `UNIMPLEMENTED` | Método no implementado |
| `INTERNAL` | Error interno |
| `RESOURCE_EXHAUSTED` | Sin recursos/rate limit |

### 3.5 “¿Qué le falta?” — checklist de RPC

1. Definir el contrato (`.proto` o método JSON-RPC).
2. Generar el código con `protoc` (gRPC).
3. Implementar el servidor.
4. Crear el **stub** en el cliente.
5. Serializar/deserializar correctamente.
6. Definir **deadline/timeout**.
7. Manejar errores con los códigos del protocolo.
8. Reintentar solo operaciones idempotentes.
9. Usar TLS en producción.
10. Versionar el contrato y no reutilizar números de campo.

### 3.6 Errores típicos en RPC

| Error | Causa | Solución |
| --- | --- | --- |
| `ModuleNotFoundError: grpc` | Falta `grpcio` | `pip install grpcio grpcio-tools` |
| `UNIMPLEMENTED` | Método no implementado o nombre mal escrito | Revisar `.proto` y servidor |
| `DEADLINE_EXCEEDED` | Timeout muy bajo u operación lenta | Aumentar deadline u optimizar |
| `UNAVAILABLE` | Servidor apagado o puerto incorrecto | Revisar host/puerto |
| `UNKNOWN` | Error de serialización/lógica | Revisar mensaje y tipos |
| `TypeError` en campos | Código generado desactualizado | Regenerar con `protoc` |
| El cliente no ve cambios | Versión de `.proto` distinta | Recompilar y desplegar ambos |

### 3.7 Ejercicios resueltos de RPC

#### E1. Completar una petición JSON-RPC

**Enunciado:** complete para llamar al método `crearJuego` con `jugador` y `numero`.

```json
{
  "jsonrpc": "2.0",
  "method": "crearJuego",
  "params": {"jugador": "ana", "numero": "4271"},
  "id": 1
}
```

**Por qué:** `jsonrpc` indica la versión; `method` el nombre; `params` los argumentos; `id` correlaciona la respuesta.

#### E2. El servidor responde `-32601`

**Respuesta:** el método no existe o está mal escrito. Comparar el nombre del cliente con el diccionario/`service` del servidor.

#### E3. `DEADLINE_EXCEEDED`

**Respuesta:** el cliente puso un timeout muy bajo o el servidor tardó demasiado. Aumentar el deadline, revisar logs y optimizar. No confundir con `UNAVAILABLE` (servidor caído).

#### E4. Mapear REST a RPC

| REST | RPC |
| --- | --- |
| `POST /login` | `AuthService.Login(LoginRequest)` |
| `POST /juego` | `JuegoService.CrearJuego(CrearJuegoRequest)` |
| `PUT /juego/{id}` | `JuegoService.Unirse(UnirseRequest)` |
| `POST /juego/{id}/jugar` | `JuegoService.Jugar(JugarRequest)` |
| `GET /juego/{id}` | `JuegoService.VerJuego(VerJuegoRequest)` |
| `GET /juego` | `JuegoService.ListarJuegos(ListarRequest)` |

#### E5. ¿Por qué no se reutilizan números de campo en protobuf?

Porque los números identifican los campos en el formato binario. Si se reutiliza un número con otro tipo, clientes viejos leen mal los datos. Se pueden marcar como `reserved`.

---

## 4. Kubernetes

### 4.1 Objetos principales

| Objeto | Qué hace |
| --- | --- |
| **Pod** | Unidad mínima; uno o más contenedores con red/volumen compartido. Es efímero. |
| **ReplicaSet** | Mantiene N réplicas de un Pod. |
| **Deployment** | Gestiona ReplicaSets, actualizaciones y rollback. |
| **StatefulSet** | Pods con identidad y almacenamiento estable. |
| **DaemonSet** | Un Pod en cada nodo. |
| **Job/CronJob** | Tareas que terminan / programadas. |
| **Service** | IP/DNS estable y balanceo hacia Pods. |
| **Ingress** | Enrutamiento HTTP/HTTPS; requiere controlador. |
| **Namespace** | Aislamiento lógico. |
| **ConfigMap** | Configuración no sensible. |
| **Secret** | Datos sensibles (base64; no cifrado por sí solo). |
| **PVC** | Almacenamiento persistente. |
| **HPA** | Escalado automático. |
| **NetworkPolicy** | Reglas de tráfico entre Pods. |

### 4.2 Deployment de clase

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    app: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-app-container
          image: nginx:1.25
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "250m"
              memory: "64Mi"
            limits:
              cpu: "500m"
              memory: "128Mi"
```

**Puntos que siempre revisa el profesor:**

- `selector.matchLabels` debe coincidir con `template.metadata.labels`. Si no, el Deployment no administra sus Pods.
- `replicas` es el número deseado.
- `containerPort` es informativo; no publica nada.
- `requests` se usa para programar; `limits` para limitar.
- Si el contenedor supera `limits.memory`, puede ser `OOMKilled`.

> **Trampa de namespace:** el YAML de clase del Deployment no trae `namespace`, pero el Service sí está en `unillanos`. Si aplicas el Deployment sin `-n unillanos`, queda en `default` y el Service no encontrará sus Pods. Agrega `metadata.namespace: unillanos` al Deployment o aplica todo con `kubectl apply -n unillanos -f ...`.

### 4.3 Service de clase

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mi-servicio
  namespace: unillanos
spec:
  type: ClusterIP
  selector:
    app: my-app
  ports:
    - protocol: TCP
      port: 80         # puerto del Service
      targetPort: 80   # puerto del contenedor
```

**Tipos:**

- **ClusterIP** (por defecto): solo dentro del clúster.
- **NodePort**: abre un puerto en cada nodo (30000–32767).
- **LoadBalancer**: IP externa del proveedor cloud.
- **ExternalName**: alias DNS a un servicio externo.

**`port` ≠ `targetPort` ≠ `nodePort`:**

- `port`: donde escucha el Service.
- `targetPort`: donde escucha el contenedor.
- `nodePort`: puerto expuesto en cada nodo (solo NodePort/LoadBalancer).

### 4.4 Deployment y Service del proyecto

El proyecto usa un `initContainer` que clona el repositorio y un contenedor `web` que instala dependencias y arranca Gunicorn:

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

**Por qué `replicas: 1` y `--workers 1`:** el estado vive en memoria. Dos Pods o dos workers tendrían partidas distintas. `strategy: Recreate` evita que durante un despliegue convivan dos versiones con estados separados.

**Por qué `emptyDir`:** comparte el código clonado entre el `initContainer` y el contenedor `web`; es temporal y se borra con el Pod.

**Rollback con `initContainer`:** `kubectl rollout undo` revierte el spec del Deployment, pero el `initContainer` vuelve a clonar el `HEAD` de GitHub. No garantiza volver al código anterior; para un rollback real hay que fijar un commit/tag o usar una imagen versionada.

### 4.5 Secret, ConfigMap y probes

**Crear un Secret:**

```bash
kubectl -n picas-y-fijas create secret generic picas-auth \
  --from-literal=signing-key="$(openssl rand -hex 32)"
```

**Usarlo como variable:**

```yaml
env:
  - name: PICAS_SECRET_KEY
    valueFrom:
      secretKeyRef:
        name: picas-auth
        key: signing-key
```

- Un Secret no es “seguro” por sí solo: por defecto se guarda base64 en etcd. Hay que proteger etcd, usar RBAC y, si se necesita, cifrado en reposo.
- Si el Secret no existe, el Pod queda en `CreateContainerConfigError`.

**Probes:**

```yaml
readinessProbe:
  httpGet:
    path: /
    port: http
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 2
  failureThreshold: 3

livenessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 15
  periodSeconds: 20
```

- **Readiness:** si falla, el Pod no recibe tráfico (pero no se reinicia).
- **Liveness:** si falla, Kubernetes reinicia el contenedor.
- **Startup:** para apps lentas; evita que liveness las mate antes de arrancar.

### 4.6 Comandos de kubectl

```bash
# Contexto y nodos
kubectl config current-context
kubectl get nodes

# Namespace
kubectl create namespace unillanos
kubectl get ns

# Aplicar/eliminar
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl delete -f deployment.yaml

# Ver recursos
kubectl -n unillanos get all
kubectl -n unillanos get pods -o wide
kubectl -n unillanos get deployments
kubectl -n unillanos get services
kubectl -n unillanos get endpoints
kubectl -n unillanos describe pod POD

# Logs
kubectl -n unillanos logs deployment/my-app
kubectl -n unillanos logs POD -c CONTENEDOR
kubectl -n unillanos logs POD --previous

# Entrar
kubectl -n unillanos exec -it POD -- sh

# Port-forward (solo depuración)
kubectl -n unillanos port-forward service/mi-servicio 8080:80

# Exponer un Deployment (forma rápida de clase)
kubectl expose deployment my-app --port=80 --target-port=80 -n unillanos

# Rollout
kubectl -n unillanos rollout status deployment/my-app
kubectl -n unillanos rollout restart deployment/my-app
kubectl -n unillanos rollout undo deployment/my-app

# Escalar
kubectl -n unillanos scale deployment/my-app --replicas=3

# Eventos
kubectl -n unillanos get events --sort-by=.metadata.creationTimestamp
```

**Secuencia completa para el proyecto:**

```bash
kubectl apply -f killercoda/namespace.yaml
kubectl -n picas-y-fijas create secret generic picas-auth \
  --from-literal=signing-key="$(openssl rand -hex 32)"
kubectl apply -f killercoda/deployment.yaml
kubectl apply -f killercoda/service.yaml
kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=300s
kubectl -n picas-y-fijas get all
kubectl -n picas-y-fijas port-forward service/picas-y-fijas --address 0.0.0.0 8080:80
```

### 4.7 “¿Qué le falta?” — checklist de Kubernetes

1. `apiVersion` y `kind` correctos.
2. `metadata.name` y `metadata.namespace`.
3. `selector.matchLabels` igual a `template.metadata.labels`.
4. `containers[].name` e `image`.
5. `containerPort` correcto.
6. `resources.requests/limits`.
7. `readinessProbe`/`livenessProbe`.
8. `Service.selector` igual a los labels del Pod.
9. `Service.targetPort` igual al puerto del contenedor.
10. Secret/ConfigMap creados **antes** de aplicar el Deployment.

### 4.8 Diagnóstico: síntoma → causa → comando

| Síntoma | Causa frecuente | Qué revisar |
| --- | --- | --- |
| `Pending` | No hay recursos, taints, PVC, selector de nodo | `kubectl describe pod`, eventos |
| `ImagePullBackOff` | Imagen mal escrita, tag inexistente, registro privado | `describe pod`, nombre/tag, secret de registro |
| `ErrImageNeverPull` | `imagePullPolicy: Never` y la imagen no está en el nodo | Cambiar política o cargar la imagen |
| `CrashLoopBackOff` | La app falla al iniciar, comando incorrecto, falta env | `logs`, `logs --previous`, `describe` |
| `CreateContainerConfigError` | Falta ConfigMap/Secret/clave | `describe pod`, crear el recurso |
| `Init:Error` / `Init:CrashLoopBackOff` | Falló un `initContainer` | Logs del initContainer |
| `RunContainerError` | Comando/binario inexistente, permisos | `describe`, `logs` |
| `OOMKilled` | Límite de memoria muy bajo | Aumentar `limits.memory`, optimizar |
| `Evicted` | Presión de memoria/disco en el nodo | Eventos, recursos |
| `READY 0/1` | Readiness probe falla | Path, puerto, tiempo de arranque |
| Service sin respuesta | Selector no coincide, `targetPort` mal, app caída | `get endpoints`, `describe service`, logs |
| `502/503` en Ingress | Sin endpoints o app no lista | `get endpoints`, readiness |
| DNS no resuelve | Nombre/namespace incorrecto | `nslookup`, FQDN |

**Flujo recomendado:**

```bash
kubectl -n NS get pods
kubectl -n NS describe pod POD
kubectl -n NS logs POD
kubectl -n NS logs POD --previous
kubectl -n NS get events --sort-by=.metadata.creationTimestamp
kubectl -n NS get endpoints
```

### 4.9 Ejercicios resueltos de Kubernetes

#### E1. El Service no encuentra los Pods

**Causa:** `spec.selector` del Service no coincide con `metadata.labels` del Pod.

```yaml
# Deployment
template:
  metadata:
    labels:
      app: picas
---
# Service
spec:
  selector:
    app: picas   # debe ser igual
```

Comprobar con `kubectl -n NS get endpoints`; si sale `<none>`, el selector está mal o los Pods no están `Ready`.

#### E2. El Service apunta al puerto equivocado

```yaml
# contenedor
ports:
  - name: http
    containerPort: 5000
---
# Service
ports:
  - port: 80
    targetPort: http   # o 5000
```

Si `targetPort: 3000` y la app escucha en `5000`, la conexión se rechaza.

#### E3. `CreateContainerConfigError`

**Causa:** el Deployment referencia un Secret/ConfigMap que no existe o una clave que no está.

```bash
kubectl -n picas-y-fijas describe pod POD
kubectl -n picas-y-fijas get secret picas-auth
kubectl -n picas-y-fijas create secret generic picas-auth \
  --from-literal=signing-key="$(openssl rand -hex 32)"
```

#### E4. La app funciona local pero no en Kubernetes

**Causa:** escucha en `127.0.0.1` dentro del contenedor. Debe escuchar en `0.0.0.0`. En el proyecto, Gunicorn usa `--bind 0.0.0.0:5000`; el servidor local de Flask usa `host="0.0.0.0"`.

#### E5. ¿Por qué no se pone `replicas: 3` en Picas y Fijas?

Porque cada Pod tiene su propio diccionario en memoria. Un jugador podría crear una partida en el Pod A y el otro no verla desde el Pod B. Para escalar haría falta una base de datos o Redis compartido, y una clave de firma común.

#### E6. Escribir un Deployment y un Service de 3 réplicas con NodePort

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:1.25
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: web
  namespace: demo
spec:
  type: NodePort
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30080
```

```bash
kubectl create namespace demo
kubectl apply -f web.yaml
kubectl -n demo get pods,svc
kubectl -n demo port-forward service/web 8080:80
```

#### E7. `port-forward` se corta

**Causa:** el proceso se terminó o el Pod se reinició. Se vuelve a ejecutar. `port-forward` es para depurar, no para producción; en producción se usa un Service `LoadBalancer` o un Ingress.

---

## 5. Simulacro integrador

### 5.0 Cómo atacar un ejercicio de “complete el código”

1. **Lee el contrato:** método, ruta, body y respuesta esperada.
2. **Identifica la pieza faltante:** middleware, validación, código de estado o header.
3. **Escribe la línea mínima** que hace funcionar el caso feliz.
4. **Prueba el caso de error:** sin token, body inválido, método equivocado.
5. **Explica qué pasa si se omite:** “sin `express.json()`, `req.body` es `undefined`”.

Si el ejercicio pide “encuentre el error”, revisa en este orden: `Content-Type` → parseo del body → validación → autenticación → autorización → código de estado → header `Location` → `0.0.0.0`.

### 5.1 API: completar el código

**Enunciado:** complete las líneas que faltan para que `POST /juego` reciba JSON, valide el número y devuelva `201`.

```js
app.______(express.json());

app.post('/juego', auth, (req, res) => {
  const { number } = req.______ || {};
  if (!validNumber(number)) {
    return res.______(400).json({ error: 'Número inválido' });
  }
  // ...
  res.______(201).json(game);
});
```

**Respuesta:** `use`, `body`, `status`, `status`. Además, `validNumber` debe comprobar `typeof n === 'string'`, `/^[0-9]{4}$/` y `new Set(n).size === 4`.

### 5.2 Dockerfile: encontrar los errores

```dockerfile
FROM node:latest
WORKDIR /app
COPY . .
RUN npm install
EXPOSE 3000
CMD npm start
```

**Errores:** imagen mutable, `COPY . .` antes de instalar, `npm install` con dev, falta `USER`, `CMD` en forma shell, falta `.dockerignore`.

**Corrección:** ver [§2.9 E1](#e1-corregir-este-dockerfile).

### 5.3 RPC: completar la petición y la respuesta

```json
{
  "______": "2.0",
  "______": "crearJuego",
  "______": {"jugador": "ana", "numero": "4271"},
  "______": 1
}
```

**Respuesta:** `jsonrpc`, `method`, `params`, `id`.

La respuesta debe tener `jsonrpc`, `result` (o `error`) e `id`.

### 5.4 Kubernetes: encontrar los errores

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: api
          image: mi-api:1.0
          ports:
            - containerPort: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api
  ports:
    - port: 80
      targetPort: 3000
```

**Errores:**

1. `template.metadata.labels` dice `app: web`, pero el selector dice `app: api`. El Deployment no administra sus Pods.
2. El Service busca `app: api`, pero los Pods tienen `app: web`; no hay endpoints.
3. `targetPort: 3000`, pero el contenedor escucha en `5000`.
4. Falta `namespace` si se aplica en uno distinto de `default`.
5. La imagen `mi-api:1.0` debe existir en el nodo o en un registro accesible.

**Corrección:** igualar labels/selectors y `targetPort: 5000`.

### 5.5 “¿Por qué falla?” — 12 escenarios

| # | Escenario | Respuesta |
| --- | --- | --- |
| 1 | `GET /juego` responde `401` | Falta `Authorization: Bearer <token>` o el token venció. |
| 2 | `POST /juego` responde `415` | Falta `Content-Type: application/json`. |
| 3 | `req.body` es `undefined` en Express | Falta `app.use(express.json())`. |
| 4 | `"0123"` se guarda como `123` | Se envió como número, no como string. |
| 5 | `POST /juego` responde `400` con `"1123"` | Dígitos repetidos; la regla exige 4 distintos. |
| 6 | `GET /juego/{id}` responde `403` | El usuario no es participante de esa partida. |
| 7 | `POST /juego/{id}/jugar` responde `403` | No es el turno del jugador. |
| 8 | Docker: `localhost:8080` no responde | La app escucha en `127.0.0.1` o falta `-p 8080:3000`. |
| 9 | Docker: `port is already allocated` | El puerto del host está ocupado; cambiar `-p` o liberarlo. |
| 10 | K8s: `CreateContainerConfigError` | Falta el Secret/ConfigMap o una clave referenciada. |
| 11 | K8s: `CrashLoopBackOff` | La app falla al iniciar; revisar `logs` y `logs --previous`. |
| 12 | K8s: Service sin respuesta | Selector no coincide, `targetPort` mal o Pods no `Ready`. |

### 5.6 Escribir desde cero

**Enunciado:** despliegue una app Node que escucha en `3000`, con 2 réplicas, Service `ClusterIP` en el puerto `80` y acceso local por `8080`.

**Solución:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: node-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: node-app
  template:
    metadata:
      labels:
        app: node-app
    spec:
      containers:
        - name: node-app
          image: mi-api:1.0
          ports:
            - containerPort: 3000
---
apiVersion: v1
kind: Service
metadata:
  name: node-app
spec:
  type: ClusterIP
  selector:
    app: node-app
  ports:
    - port: 80
      targetPort: 3000
```

```bash
kubectl apply -f node-app.yaml
kubectl get pods,svc
kubectl port-forward service/node-app 8080:80
```

---

## 6. Teoría mínima para responder

| Pregunta | Respuesta corta |
| --- | --- |
| ¿Qué es una API? | Un contrato entre componentes que define operaciones, datos y errores. |
| ¿Qué es REST? | Un estilo arquitectónico basado en recursos, HTTP, stateless e interfaz uniforme. |
| ¿Qué es un endpoint? | Método HTTP + ruta; por ejemplo `POST /juego`. |
| ¿Qué es stateless? | El servidor no guarda sesión entre peticiones; cada una trae su token. |
| ¿Qué es idempotente? | Repetir la operación produce el mismo estado final. |
| ¿401 vs 403? | 401 = no autenticado; 403 = autenticado pero sin permiso. |
| ¿Qué es Docker? | Una plataforma para empaquetar y ejecutar aplicaciones en contenedores. |
| ¿Imagen vs contenedor? | Imagen = plantilla; contenedor = instancia en ejecución. |
| ¿Qué es un Dockerfile? | La receta para construir una imagen. |
| ¿Qué hace `EXPOSE`? | Documenta el puerto; no lo publica. |
| ¿Qué es RPC? | Llamar una función remota como si fuera local. |
| ¿REST vs RPC? | REST modela recursos; RPC modela acciones. |
| ¿Qué es gRPC? | RPC de Google con protobuf y HTTP/2. |
| ¿Qué es un Pod? | La unidad mínima de Kubernetes; uno o más contenedores. |
| ¿Qué hace un Deployment? | Mantiene réplicas y gestiona actualizaciones/rollback. |
| ¿Qué hace un Service? | Da una IP/DNS estable y balancea hacia los Pods. |
| ¿`port` vs `targetPort`? | `port` es del Service; `targetPort` es del contenedor. |
| ¿Qué es un Namespace? | Aislamiento lógico de recursos. |
| ¿Qué es un Secret? | Objeto para datos sensibles; base64 no es cifrado. |
| ¿Qué es una probe? | Comprobación de salud; readiness saca de endpoints, liveness reinicia. |
| ¿Qué es `port-forward`? | Túnel local para depurar; no es producción. |

---

## 7. Checklist final (10 minutos antes)

- [ ] Sé la diferencia entre `401` y `403`.
- [ ] Sé que `express.json()` es obligatorio para `req.body`.
- [ ] Sé que `number` va como **string** para conservar `"0123"`.
- [ ] Sé validar 4 dígitos distintos en JS y Python.
- [ ] Sé escribir un Dockerfile de Node con `COPY package*.json`, `npm ci`, `USER`, `CMD` exec.
- [ ] Sé que `-p 8080:3000` es host:contenedor y que `EXPOSE` no publica.
- [ ] Sé que la app debe escuchar en `0.0.0.0`.
- [ ] Sé la diferencia entre REST y RPC.
- [ ] Sé completar una petición JSON-RPC (`jsonrpc`, `method`, `params`, `id`).
- [ ] Sé que `selector.matchLabels` debe coincidir con los labels del Pod.
- [ ] Sé que `targetPort` debe coincidir con el puerto del contenedor.
- [ ] Sé diagnosticar `Pending`, `ImagePullBackOff`, `CrashLoopBackOff`, `CreateContainerConfigError` y `READY 0/1`.
- [ ] Sé la secuencia `namespace → secret → deployment → service → rollout → port-forward`.
- [ ] Sé por qué Picas y Fijas usa una réplica y un worker: estado en memoria.
- [ ] Sé que un Secret no está cifrado por sí solo.

---

## 8. Autoevaluación relámpago

> Tapa la columna de respuesta. Si fallas una, vuelve a la sección indicada.

| # | Pregunta | Respuesta | Repasar |
| --- | --- | --- | --- |
| 1 | ¿Qué middleware parsea JSON en Express? | `app.use(express.json())`; sin él, `req.body` es `undefined`. | §1.3 |
| 2 | ¿Qué código y header devuelve una creación exitosa? | `201` + `Location`. | §1.7 |
| 3 | Token válido, pero no es tu turno: ¿401 o 403? | `403`. | §1.8 |
| 4 | Falta el header `Authorization`: ¿401 o 403? | `401`. | §1.8 |
| 5 | ¿Por qué `"0123"` viaja como string? | Conserva el cero inicial; `Number("0123")` es `123`. | §1.6 |
| 6 | ¿Cómo se calculan las picas? | Dígitos del intento que están en el secreto, menos las fijas. | §1.6 |
| 7 | ¿Qué hace `-p 8080:3000`? | Publica el 8080 del host hacia el 3000 del contenedor. | §2.5 |
| 8 | ¿Qué publica `EXPOSE 3000`? | Nada; solo documenta el puerto. | §2.2 |
| 9 | ¿Por qué escuchar en `0.0.0.0`? | Acepta conexiones de fuera del contenedor; `127.0.0.1` solo acepta locales. | §2.8 |
| 10 | ¿Imagen vs contenedor? | Imagen = plantilla de solo lectura; contenedor = instancia en ejecución. | §2.1 |
| 11 | ¿Qué usuario usa el Dockerfile de clase? | `USER node`, para no correr como root. | §2.2 |
| 12 | ¿Qué pasa si `npm ci` no encuentra `package-lock.json`? | Falla; usa `npm install --omit=dev` o genera el lock. | §2.9 |
| 13 | ¿Miembros de una petición JSON-RPC? | `jsonrpc`, `method`, `params`, `id`. | §3.2 |
| 14 | ¿Qué significa el error `-32601`? | `Method not found`. | §3.4 |
| 15 | ¿Qué transporte y serialización usa gRPC? | HTTP/2 y protobuf. | §3.3 |
| 16 | ¿`DEADLINE_EXCEEDED` vs `UNAVAILABLE`? | Timeout del cliente vs servidor no disponible. | §3.6 |
| 17 | ¿Qué pasa si `selector.matchLabels` no coincide con los labels del Pod? | El Deployment no administra sus Pods. | §4.2 |
| 18 | ¿`port` vs `targetPort`? | `port` es del Service; `targetPort` es del contenedor. | §4.3 |
| 19 | ¿Qué revisas si el Service no responde? | `get endpoints`, selector, `targetPort` y readiness. | §4.8 |
| 20 | ¿Qué causa `CreateContainerConfigError`? | Falta un Secret/ConfigMap o una clave referenciada. | §4.8 |
| 21 | ¿Primer comando ante `CrashLoopBackOff`? | `kubectl logs` y `logs --previous`. | §4.8 |
| 22 | ¿Causas de `Pending`? | Recursos, taints, PVC o selector de nodo. | §4.8 |
| 23 | ¿Por qué Picas y Fijas usa `replicas: 1`? | Estado en memoria; dos Pods tendrían partidas distintas. | §4.4 |
| 24 | ¿Qué pasa si aplicas el Deployment de clase sin `-n unillanos`? | Queda en `default` y el Service no lo encuentra. | §4.2 |
| 25 | ¿Un Secret está cifrado? | No; base64 en etcd, sin cifrado por sí solo. | §4.5 |
| 26 | ¿Readiness vs liveness? | Readiness saca de endpoints; liveness reinicia el contenedor. | §4.5 |
| 27 | ¿`rollout undo` restaura el código del initContainer? | No; el initContainer sigue clonando el `HEAD`. | §4.4 |
| 28 | ¿`port-forward` es para producción? | No; es un túnel de depuración. | §4.6 |
| 29 | ¿Qué devuelve `GET /juego` en el proyecto? | Resumen: `id`, `creator`, `players`, `status`, `winner`. | §4.4 |
| 30 | ¿Qué método usa el proyecto para unirse? | `PUT /juego/{id}` (semánticamente sería `POST /juego/{id}/jugadores`). | §4.4 |

## 9. Trampas que más cuestan puntos

1. **Confundir `401` con `403`.** `401` es “no sé quién eres”; `403` es “sé quién eres, pero no puedes”.
2. **Olvidar `express.json()`.** Sin el middleware, `req.body` no existe aunque el JSON sea válido.
3. **Mandar el número como número.** `0123` se convierte en `123`; siempre string.
4. **Creer que `EXPOSE` publica.** Se publica con `-p`; `EXPOSE` solo documenta.
5. **Poner `targetPort` igual al `port` sin mirar el contenedor.** Debe coincidir con el puerto real de la app.
6. **Cambiar labels sin cambiar el selector.** El Deployment y el Service dejan de encontrar los Pods.
7. **Creer que un Secret cifra.** Es base64; hay que proteger etcd, usar RBAC y cifrado en reposo.
8. **Poner `replicas: 3` en Picas y Fijas.** Sin estado compartido, cada Pod tendría partidas distintas.
9. **Usar `latest` sin justificar.** En producción conviene una versión fija y, si se puede, un digest.
10. **Decir “REST es mejor que RPC”.** Di “REST encaja mejor con el navegador; RPC/gRPC con comunicación interna y rendimiento”.

### 9.1 Respuesta modelo para un “¿por qué falla?”

> “El cliente recibe `415` porque el `Content-Type` no es `application/json`. Flask no parsea el body y lo rechaza antes de llegar a la ruta. Se corrige enviando `Content-Type: application/json`; si fuera Express, además haría falta `app.use(express.json())`.”

Estructura: **síntoma → causa → por qué → corrección → cómo verifico**.

---

> **Documento complementario:** `01_teoria_api_docker_rpc_kubernetes.md` explica el “por qué” con más detalle; `03_sustentacion_proyecto.md` es el guion para defender Picas y Fijas.
