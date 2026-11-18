# Teoría para el parcial: API, Docker, RPC y Kubernetes

> Documento de estudio basado en el proyecto **Picas y Fijas**, en los documentos de clase (`k8s.docx`, `server.js` y `Dockerfile` de Node) y en el enunciado del juego distribuido.
>
> La idea no es solo memorizar: cada tema termina con **cómo lo usa el proyecto**, **errores típicos** y **preguntas que puede hacer el profesor**. Los ejercicios prácticos están en `02_apunte_parcial.md`.

## Cómo repasar este documento

| Pasada | Tiempo | Qué hacer |
| --- | --- | --- |
| **1. Conceptos** | 40 min | Lee cada sección y explícala en voz alta en una frase. Si no puedes, vuelve al párrafo. |
| **2. Proyecto** | 20 min | Para cada tema, di qué archivo lo implementa y qué decisión se tomó. |
| **3. Examen** | 30 min | Tapa las respuestas de §8, responde en voz alta y luego resuelve los ejercicios de `02_apunte_parcial.md`. |

**Regla de estudio:** no releas pasivamente. Cierra el documento y escribe de memoria: los cuatro temas, seis códigos HTTP, los cinco pasos del despliegue y tres diferencias entre REST y RPC.

---

## Índice

1. [Contexto: sistemas distribuidos](#1-contexto-sistemas-distribuidos)
2. [API y REST](#2-api-y-rest)
3. [Docker](#3-docker)
4. [RPC](#4-rpc)
5. [Kubernetes](#5-kubernetes)
6. [Cómo se integran los cuatro temas en Picas y Fijas](#6-cómo-se-integran-los-cuatro-temas-en-picas-y-fijas)
7. [Chuleta de comandos](#7-chuleta-de-comandos)
8. [Preguntas típicas con respuesta corta](#8-preguntas-típicas-con-respuesta-corta)
9. [Glosario](#9-glosario)

---

## 1. Contexto: sistemas distribuidos

Un **sistema distribuido** es un conjunto de procesos que se ejecutan en máquinas distintas y se comunican por red para dar la impresión de ser un solo sistema. El proyecto es distribuido porque el navegador de cada jugador, el servidor Flask y el Pod de Kubernetes son procesos separados que intercambian mensajes HTTP.

### 1.1 Características que hay que tener presentes

- **No hay memoria compartida**: cada proceso tiene su propio estado. Dos jugadores no pueden leer la variable `game` del otro; todo pasa por la API.
- **La red no es instantánea**: hay latencia, pérdida de paquetes, timeouts y errores parciales.
- **Los fallos son parciales**: puede caerse un Pod, el navegador, o la red, sin que se caiga todo el sistema.
- **Concurrencia**: dos peticiones pueden llegar al mismo tiempo. Hay que decidir qué pasa si dos jugadores intentan unirse o jugar a la vez.
- **Estado**: un servicio es **stateless** si no guarda estado entre peticiones (cada petición trae su token); es **stateful** si depende de estado almacenado (las partidas en memoria del proyecto).

### 1.2 Las falacias de la computación distribuida

Son suposiciones falsas que causan muchos errores:

1. La red es confiable.
2. La latencia es cero.
3. El ancho de banda es infinito.
4. La red es segura.
5. La topología no cambia.
6. Hay un solo administrador.
7. El costo de transporte es cero.
8. La red es homogénea.

Por eso se usan **timeouts**, **reintentos con backoff**, **idempotencia**, **validación** y **manejo de errores** en la API.

### 1.3 Monolito, capas y microservicios

- **Monolito**: una sola aplicación despliega todo. Es más simple de desarrollar y depurar.
- **Microservicios**: varios servicios pequeños e independientes. Escalan por separado, pero añaden complejidad de red, observabilidad y consistencia.
- **Arquitectura por capas** (la del proyecto): rutas → servicios → dominio → repositorios. Cada capa tiene una responsabilidad y se puede probar o reemplazar por separado.

### 1.4 Dónde encaja cada tecnología

| Tecnología | Pregunta que responde |
| --- | --- |
| **API REST** | ¿Cómo se comunican el cliente y el servidor? |
| **Docker** | ¿Cómo empaqueto y ejecuto la aplicación de forma reproducible? |
| **RPC** | ¿Cómo llamo una función remota de forma directa y eficiente? |
| **Kubernetes** | ¿Cómo ejecuto, expongo y recupero contenedores en un clúster? |

### 1.5 Errores conceptuales que más se confunden

| Confusión frecuente | Corrección |
| --- | --- |
| “REST es un protocolo” | REST es un **estilo arquitectónico**; el protocolo es HTTP. |
| “API = REST” | La API es el **contrato**; REST es una forma de diseñarla. También existe RPC. |
| “401 es falta de permiso” | `401` = no autenticado o credencial inválida. `403` = autenticado sin permiso. |
| “POST siempre crea” | `POST` puede crear **o ejecutar una acción**; no es idempotente. |
| “PUT actualiza parcialmente” | `PUT` **reemplaza**; `PATCH` actualiza parcialmente. |
| “Docker es una máquina virtual” | El contenedor **comparte el kernel**; no incluye un SO completo. |
| “`EXPOSE` publica el puerto” | Solo lo **documenta**. Se publica con `-p host:contenedor`. |
| “`containerPort` abre el puerto” | Es informativo para el Pod y el Service; no publica nada. |
| “Un Secret está cifrado” | Se guarda en **base64**; no es cifrado por sí solo. |
| “El Service balancea por IP” | Selecciona Pods por **labels** y usa sus endpoints. |
| “`port-forward` es para producción” | Es un **túnel de depuración**; en producción se usa Ingress o LoadBalancer. |
| “RPC es mejor que REST” | Depende: RPC brilla en acciones, contratos fuertes y rendimiento; REST en recursos y navegador. |

---

## 2. API y REST

### 2.1 ¿Qué es una API?

Una **API** (*Application Programming Interface*) es un contrato entre dos componentes: define qué operaciones existen, qué datos reciben, qué devuelven y qué errores pueden ocurrir. Una **API web** usa HTTP como transporte y normalmente JSON como formato.

Conceptos:

- **Endpoint**: combinación de método HTTP + ruta. Ejemplo: `POST /juego`.
- **Recurso**: objeto o colección que se manipula. Ejemplo: `/juego`, `/juego/{id}`.
- **Petición**: método, ruta, headers, query params y body.
- **Respuesta**: código de estado, headers y body.
- **Cliente**: navegador, `curl`, Postman, otra aplicación.
- **Servidor**: Flask, Express, etc.

### 2.2 HTTP a fondo

Una petición HTTP tiene:

```http
POST /juego HTTP/1.1
Host: localhost:5000
Authorization: Bearer eyJ...
Content-Type: application/json

{"number":"4271"}
```

Una respuesta:

```http
HTTP/1.1 201 CREATED
Content-Type: application/json
Location: /juego/482913

{"id":"482913","creator":"ana","players":["ana"],"status":"waiting","turn":null,"attempts":[],"winner":null}
```

#### Métodos HTTP

| Método | Uso | ¿Seguro? | ¿Idempotente? |
| --- | --- | --- | --- |
| `GET` | Leer un recurso | Sí | Sí |
| `HEAD` | Como GET, sin body | Sí | Sí |
| `POST` | Crear o ejecutar una acción | No | No |
| `PUT` | Reemplazar/actualizar un recurso | No | Sí |
| `PATCH` | Actualizar parcialmente | No | No necesariamente |
| `DELETE` | Eliminar | No | Sí |
| `OPTIONS` | Consultar capacidades/CORS | Sí | Sí |

- **Seguro**: no modifica el estado del servidor.
- **Idempotente**: repetir la misma petición produce el mismo efecto final. `POST /juego` no es idempotente: dos llamadas crean dos partidas. `PUT /juego/{id}` sí debería serlo.
- En el proyecto, `POST /juego/{id}/jugar` es una acción y no es idempotente: cada intento cuenta y cambia el turno.

#### Códigos de estado

| Código | Significado | Cuándo usarlo |
| --- | --- | --- |
| `200 OK` | Éxito | GET, PUT, POST que devuelven datos |
| `201 Created` | Recurso creado | POST que crea, con header `Location` |
| `202 Accepted` | Aceptado para procesar | Procesamiento asíncrono |
| `204 No Content` | Éxito sin body | DELETE o actualización sin respuesta |
| `301/308` | Redirección permanente | Cambio de URL |
| `302/307` | Redirección temporal | Login, redirecciones |
| `304 Not Modified` | Caché válida | GET condicional con ETag |
| `400 Bad Request` | Petición inválida | JSON mal formado, número inválido, transición inválida |
| `401 Unauthorized` | No autenticado | Falta token, token inválido o vencido |
| `403 Forbidden` | Autenticado pero sin permiso | No es tu turno, no eres participante |
| `404 Not Found` | No existe | Partida inexistente o ruta inexistente |
| `405 Method Not Allowed` | Método no permitido | `DELETE /juego` si no existe |
| `406 Not Acceptable` | Formato no aceptado | `Accept` no soportado |
| `409 Conflict` | Conflicto con el estado | Unirse a partida llena (el proyecto usa 400) |
| `410 Gone` | Recurso eliminado definitivamente | — |
| `413 Payload Too Large` | Body demasiado grande | — |
| `415 Unsupported Media Type` | Content-Type incorrecto | Enviar formulario donde se espera JSON |
| `422 Unprocessable Entity` | Sintaxis correcta, semántica inválida | Validación de campos |
| `429 Too Many Requests` | Rate limit | — |
| `500 Internal Server Error` | Error del servidor | Excepción no controlada |
| `501 Not Implemented` | No implementado | — |
| `502 Bad Gateway` | Proxy recibió respuesta inválida | — |
| `503 Service Unavailable` | Servicio no disponible | Sobrecarga o mantenimiento |
| `504 Gateway Timeout` | Timeout del proxy | — |

**Regla de oro:** el código debe reflejar la causa. Si el cliente no mandó token → `401`; si mandó token pero no es su turno → `403`; si el número es inválido → `400`; si la partida no existe → `404`.

#### Headers importantes

| Header | Para qué |
| --- | --- |
| `Content-Type` | Formato del body enviado (`application/json`) |
| `Accept` | Formato que el cliente acepta |
| `Authorization` | Credenciales (`Bearer TOKEN`) |
| `Location` | URL del recurso creado (`201`) |
| `Cache-Control` | Política de caché |
| `ETag` / `If-None-Match` | Validación de caché |
| `Retry-After` | Cuándo reintentar (`429`/`503`) |
| `X-Request-ID` | Trazabilidad |
| `Access-Control-Allow-Origin` | CORS |

### 2.3 REST

**REST** (*Representational State Transfer*) es un estilo arquitectónico descrito por Roy Fielding. No es un protocolo ni una librería: es un conjunto de restricciones para diseñar APIs.

Restricciones principales:

1. **Cliente-servidor**: separación de responsabilidades.
2. **Sin estado (stateless)**: cada petición contiene toda la información necesaria; el servidor no guarda sesión entre peticiones. El proyecto usa un token firmado en cada petición.
3. **Cacheable**: las respuestas pueden indicar si se pueden cachear.
4. **Interfaz uniforme**: recursos identificados por URL, manipulación mediante representaciones, mensajes autodescriptivos, HATEOAS (opcional).
5. **Sistema en capas**: proxies, balances, gateways.
6. **Código bajo demanda** (opcional): el servidor puede enviar código ejecutable.

#### Recursos y rutas

Se usan **sustantivos** y jerarquía:

```text
GET    /juego              → lista de partidas
POST   /juego              → crear partida
GET    /juego/{id}         → ver una partida
PUT    /juego/{id}         → unirse a una partida
POST   /juego/{id}/jugar   → ejecutar una jugada
POST   /login              → iniciar sesión
```

`/juego/{id}/jugar` es una **acción**; en REST puro se discutiría, pero es una convención aceptada para operaciones que no son CRUD. Lo importante es que el contrato sea claro y consistente.

#### Buenas prácticas de diseño

- Sustantivos consistentes con el recurso: `/juego`, no `/crearJuego`.
- No poner verbos en la URL si se puede modelar como recurso: `POST /juego` en vez de `/crear-juego`.
- Versionar si la API va a cambiar: `/v1/juego`.
- Devolver errores consistentes: `{"error": "..."}`.
- Usar `201` + `Location` al crear.
- No devolver datos sensibles (el proyecto no devuelve los números secretos).
- Validar tipos, longitudes y reglas de negocio.
- Paginar listados grandes (`?limit=20&offset=0`).
- Documentar con OpenAPI/Swagger.
- Usar HTTPS en producción.
- Limitar tamaño de body, timeouts y rate limiting.

### 2.4 JSON

JSON es un formato de texto para representar datos:

```json
{
  "id": "482913",
  "creator": "ana",
  "players": ["ana", "luis"],
  "status": "in_progress",
  "turn": "luis",
  "attempts": [],
  "winner": null
}
```

Reglas:

- Los strings van entre comillas dobles.
- Los números no llevan ceros a la izquierda (`0123` no es un número JSON válido).
- `null` es distinto de `""` y de `0`.
- No hay comentarios.
- El `Content-Type` debe ser `application/json`.
- En Python, `json.dumps`/`jsonify` serializan; `request.get_json()` deserializa.
- En JavaScript, `JSON.stringify`/`JSON.parse`.

Por eso el número secreto se envía como **string** (`"0123"`) y no como número: se conservan los ceros iniciales y se valida mejor.

### 2.5 Autenticación y autorización

- **Autenticación**: ¿quién eres? (login).
- **Autorización**: ¿qué puedes hacer? (permisos).

Mecanismos habituales:

| Mecanismo | Idea | Ventaja | Riesgo |
| --- | --- | --- | --- |
| Basic | `usuario:password` en Base64 | Simple | Debe ir siempre con HTTPS; no hay logout real |
| Sesión/cookie | ID de sesión en cookie | Fácil de revocar | Requiere almacenamiento de sesiones; CSRF |
| Bearer token | Token en `Authorization` | Stateless | Si se filtra, sirve hasta vencer |
| JWT | Token firmado con claims | Estándar, verificable | No está cifrado; no meter secretos |
| Token firmado | Firma HMAC + timestamp | Simple y sin estado | Hay que proteger la clave |

En el proyecto:

```python
serializer = URLSafeTimedSerializer(secret_key, salt="picas-y-fijas-auth")
token = serializer.dumps({"username": username})
data = serializer.loads(token, max_age=3600)
```

- El token está **firmado**, no cifrado: cualquiera puede leer el username, pero no modificarlo sin la clave.
- `max_age=3600` = una hora.
- La clave se toma de `PICAS_SECRET_KEY`; si no existe, se genera una aleatoria al arrancar.
- El servidor es **stateless** para autenticar: no guarda sesiones; verifica la firma en cada petición.
- **Cerrar sesión** en el front solo borra el token de la pestaña; el token copiado sigue siendo válido hasta que vence o cambia la clave.

**401 vs 403:**

- `401`: no sé quién eres / tu credencial no es válida → vuelve a autenticarte.
- `403`: sé quién eres, pero no tienes permiso → no insistas con otra credencial.

### 2.6 Manejo de errores

Una API debe devolver errores **en el mismo formato** que las respuestas exitosas. En el proyecto:

```json
{"error": "No es tu turno"}
```

```json
{"error": "Not Found", "description": "The requested URL was not found on the server."}
```

Buenas prácticas:

- No devolver HTML de error en una API JSON.
- No filtrar stack traces ni datos internos en producción.
- Usar códigos HTTP correctos.
- Incluir un mensaje útil pero sin secretos.
- Registrar el error en logs con un ID de correlación.
- Validar antes de tocar el estado.

Mapa de errores del proyecto:

| Excepción | HTTP |
| --- | --- |
| `NotFoundError` | 404 |
| `UnauthorizedError` | 401 |
| `ForbiddenError` | 403 |
| `DomainError` | 400 |
| `ValueError` | 400 |
| `HTTPException` (405, 415, etc.) | El código de la excepción |

### 2.7 Cómo se implementa una API en Flask

Flask es un microframework de Python. El proyecto usa una **app factory** y **blueprints**.

```python
from flask import Flask, Blueprint, jsonify, request

game_bp = Blueprint("game", __name__, url_prefix="/juego")

@game_bp.post("")
def create_game():
    data = request.get_json()
    if not isinstance(data, dict):
        raise ValueError("El cuerpo debe ser un objeto JSON")
    # ... lógica ...
    return jsonify(game.to_dict()), 201, {"Location": f"/juego/{game.id}"}

def create_app():
    app = Flask(__name__)
    app.register_blueprint(game_bp)
    return app
```

Conceptos:

- `request.get_json()`: deserializa el body JSON.
- `jsonify(...)`: devuelve JSON con `Content-Type: application/json`.
- `return body, status, headers`: respuesta completa.
- `Blueprint`: agrupa rutas.
- `url_for`: genera URLs.
- `g`: contexto de la petición (el decorador guarda `g.username`).
- `app.test_client()`: cliente de pruebas sin levantar servidor.
- `app.errorhandler`: convierte excepciones en respuestas HTTP.

### 2.8 Cómo se implementa una API en Express (clase)

El archivo `DOC-20261109-WA0086` es un servidor mínimo:

```js
const express = require('express');

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.send('Hello World from Express in Docker! 🐳');
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
```

Para una API real faltan piezas que el profesor puede pedir:

```js
app.use(express.json()); // parsear JSON

app.post('/login', (req, res) => {
  const { username } = req.body;
  if (!username) return res.status(400).json({ error: 'username es obligatorio' });
  res.json({ token: '...' });
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});
```

- `express.json()` es el middleware que lee el body JSON; sin él, `req.body` no tiene los datos.
- `res.status(...).json(...)` devuelve código + JSON.
- `process.env.PORT` permite configurar el puerto en Docker/Kubernetes.
- `app.listen(PORT)` debe escuchar en `0.0.0.0` dentro de un contenedor (por defecto Express escucha en todas las interfaces, pero si se pone `localhost` falla).

### 2.9 Probar una API con cURL

```bash
# Login
curl -i -X POST http://localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"ana"}'

# Crear partida
curl -i -X POST http://localhost:5000/juego \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"number":"4271"}'

# Unirse
curl -i -X PUT http://localhost:5000/juego/482913 \
  -H 'Authorization: Bearer TOKEN_LUIS' \
  -H 'Content-Type: application/json' \
  -d '{"username":"luis","number":"0123"}'

# Jugar
curl -i -X POST http://localhost:5000/juego/482913/jugar \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"number":"1234"}'
```

### 2.10 Errores típicos en APIs

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| `415 Unsupported Media Type` | Falta `Content-Type: application/json` | Agregar el header |
| `400 Bad Request` por JSON | JSON mal formado o body no es objeto | Validar con `request.get_json()` y `isinstance(dict)` |
| `401` siempre | No se envía `Authorization: Bearer ...` o el token venció | Revisar header, relogin |
| `403` | Usuario autenticado pero no participante o no es su turno | Revisar lógica de permisos |
| `404` | ID incorrecto o ruta mal escrita | Revisar URL y recurso |
| `405` | Método HTTP equivocado | Usar el método de la tabla |
| `500` | Excepción no controlada | Ver logs y reproducir |
| El body llega vacío | Falta `express.json()` o `Content-Type` | Agregar middleware/header |
| `0123` se convierte en `123` | Se envió como número, no como string | Enviar `"0123"` |
| CORS bloquea el navegador | Origen distinto y no hay headers CORS | Configurar CORS o usar el mismo origen |

---

## 3. Docker

### 3.1 ¿Qué problema resuelve?

Docker empaqueta una aplicación con sus dependencias en una **imagen** reproducible. Así se evita el clásico “en mi máquina sí funciona”.

- **Imagen**: plantilla de solo lectura, construida por capas.
- **Contenedor**: instancia en ejecución de una imagen; tiene una capa escribible y su propio sistema de archivos, red y procesos.
- **Registro**: lugar donde se publican imágenes (Docker Hub, GHCR, ECR, etc.).
- **Dockerfile**: receta para construir la imagen.
- **Volumen**: almacenamiento persistente fuera del contenedor.
- **Red**: los contenedores se comunican por nombre de servicio en Docker Compose.

Diferencia con una máquina virtual:

| VM | Contenedor |
| --- | --- |
| Hipervisor + SO completo | Comparte el kernel del host |
| Más pesada | Más liviana |
| Aislamiento más fuerte | Aislamiento por namespaces/cgroups |
| Arranque lento | Arranque rápido |

### 3.2 Dockerfile

Instrucciones principales:

| Instrucción | Para qué |
| --- | --- |
| `FROM` | Imagen base |
| `WORKDIR` | Directorio de trabajo |
| `COPY` | Copiar archivos del contexto |
| `ADD` | Como COPY, pero también URLs/tar (preferir COPY) |
| `RUN` | Ejecutar comandos durante el build (crea capa) |
| `ENV` | Variables de entorno persistentes |
| `ARG` | Variables solo durante el build |
| `EXPOSE` | Documenta el puerto (no lo publica) |
| `USER` | Usuario con el que corre el contenedor |
| `CMD` | Comando por defecto; puede ser sobrescrito |
| `ENTRYPOINT` | Ejecutable fijo; los argumentos se agregan |
| `HEALTHCHECK` | Comando para comprobar salud |
| `VOLUME` | Punto de montaje persistente |

Ejemplo de la clase (`DOC-20261109-WA0087`):

```dockerfile
# Use official lightweight Node.js image
FROM node:26-alpine3.22

# Set working directory
WORKDIR /app

# Generate package.json and install express in one step
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

Análisis:

- `FROM node:26-alpine3.22`: imagen base ligera. En producción conviene fijar una versión estable y, si es posible, un digest.
- `WORKDIR /app`: todo se ejecuta allí.
- `RUN npm ...`: instala dependencias durante el build. Si se copia primero `package.json` y luego el código, se aprovecha la caché.
- `COPY . .`: copia el resto del proyecto. Sin `.dockerignore`, puede copiar `node_modules`, `.git`, etc.
- `EXPOSE 3000`: documenta el puerto; para acceder hay que publicarlo con `-p`.
- `USER node`: buena práctica, no correr como root.
- `CMD ["npm","start"]`: forma exec, recomendada para recibir señales correctamente.

Mejoras típicas:

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

Y un `.dockerignore`:

```text
node_modules
npm-debug.log
.git
.gitignore
Dockerfile
README.md
```

### 3.3 Construir, ejecutar y depurar

```bash
# Construir
docker build -t mi-api:1.0 .

# Ejecutar publicando el puerto 3000 del contenedor en el 8080 del host
docker run --rm -p 8080:3000 --name mi-api mi-api:1.0

# En segundo plano
docker run -d -p 8080:3000 --name mi-api mi-api:1.0

# Ver contenedores
docker ps
docker ps -a

# Logs
docker logs -f mi-api

# Entrar al contenedor
docker exec -it mi-api sh

# Detener/eliminar
docker stop mi-api
docker rm mi-api

# Imágenes
docker images
docker rmi mi-api:1.0
```

Variables de entorno:

```bash
docker run --rm -p 8080:3000 -e PORT=3000 mi-api:1.0
```

Volúmenes:

```bash
docker run --rm -v "$PWD":/app -w /app node:20-alpine node server.js
```

Docker Compose:

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

### 3.4 Buenas prácticas

- Usar imágenes base mínimas y versionadas (no `latest` en producción).
- Ordenar el Dockerfile para aprovechar la caché: dependencias antes que código.
- Ejecutar como usuario no root (`USER`).
- No copiar secretos a la imagen; usar variables de entorno o secretos.
- Un proceso por contenedor (idealmente).
- Usar `.dockerignore`.
- Agregar `HEALTHCHECK`.
- Multi-stage build para separar compilación y runtime.
- Etiquetar imágenes con versión (`mi-api:1.0.0`), no solo `latest`.
- Escanear vulnerabilidades (`docker scout`, Trivy).

### 3.5 Errores típicos en Docker

| Error | Causa | Solución |
| --- | --- | --- |
| `COPY failed: file not found` | El archivo no está en el contexto de build | Revisar ruta y `.dockerignore` |
| `port is already allocated` | El puerto del host está ocupado | Cambiar `-p` o liberar el puerto |
| `exec format error` | Imagen de otra arquitectura | Usar `--platform` o build multiplataforma |
| El contenedor sale inmediatamente | El comando principal terminó o falló | `docker logs`, revisar `CMD` |
| `permission denied` | Usuario sin permisos | Ajustar `USER`/permisos de archivos |
| No se puede acceder desde el host | La app escucha en `127.0.0.1` dentro del contenedor | Escuchar en `0.0.0.0` |
| `Cannot find module` | Faltó copiar dependencias o `node_modules` | `npm ci` en el Dockerfile |
| Cambios no se reflejan | Caché o falta rebuild | `docker build --no-cache` |
| Imagen enorme | Se copió todo el contexto | `.dockerignore`, multi-stage |

### 3.6 Cómo se relaciona con Picas y Fijas

El proyecto **no incluye Dockerfile**. En Kubernetes se usa directamente la imagen oficial `python:3.12-slim` y el contenedor instala las dependencias al arrancar:

```yaml
image: python:3.12-slim
command: ["/bin/sh", "-ec"]
args:
  - |
    pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0
    exec gunicorn --bind 0.0.0.0:5000 --workers 1 run:app
```

Eso funciona para la demo, pero no es lo ideal en producción: cada arranque descarga paquetes y depende de PyPI. Una versión con Dockerfile sería:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0
COPY run.py .
COPY app ./app
RUN useradd -m appuser && chown -R appuser /app
USER appuser
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "run:app"]
```

Si el profesor pide “dockerice el proyecto”, esa es la respuesta.

---

## 4. RPC

### 4.1 ¿Qué es RPC?

**RPC** (*Remote Procedure Call*) permite llamar una función que se ejecuta en otro proceso o máquina como si fuera local:

```python
resultado = juego.crear_juego("ana", "4271")
```

Pero por debajo hay red, serialización, timeouts y errores. El objetivo es **ocultar la complejidad** de la comunicación.

Componentes:

- **Cliente / stub**: objeto local que envuelve la llamada y envía la petición.
- **Servidor / skeleton**: recibe, deserializa, ejecuta el método y responde.
- **IDL** (*Interface Definition Language*): archivo que define métodos, parámetros y tipos (ej. `.proto` en gRPC).
- **Marshalling/serialization**: convertir objetos a bytes/JSON/protobuf y viceversa.
- **Transporte**: TCP, HTTP/1.1, HTTP/2, etc.
- **Registro/descubrimiento**: cómo el cliente encuentra el servidor.

### 4.2 RPC vs REST

| Aspecto | REST | RPC |
| --- | --- | --- |
| Modelo | Recursos y representaciones | Acciones/métodos |
| Interfaz | HTTP + URL + métodos | IDL + stubs |
| Acoplamiento | Más débil | Más fuerte (contrato) |
| Formato | JSON/XML normalmente | JSON, protobuf, binario |
| Rendimiento | Bueno | Muy bueno con binario/HTTP2 |
| Streaming | Limitado | gRPC soporta 4 modos |
| Navegador | Nativo | gRPC-Web o JSON-RPC |
| Cache HTTP | Aprovecha caché | Menos directo |
| Ejemplos | `/juego/123` | `JuegoService.CrearJuego(...)` |

**No hay uno mejor siempre**: REST es ideal para APIs públicas y recursos; RPC/gRPC es ideal para comunicación interna entre servicios, alto rendimiento y contratos fuertes.

### 4.3 JSON-RPC

JSON-RPC 2.0 es un protocolo simple sobre JSON. No impone transporte (puede ser HTTP, WebSocket, TCP).

Petición:

```json
{
  "jsonrpc": "2.0",
  "method": "crearJuego",
  "params": {"jugador": "ana", "numero": "4271"},
  "id": 1
}
```

Respuesta exitosa:

```json
{
  "jsonrpc": "2.0",
  "result": {"id": "482913", "estado": "waiting"},
  "id": 1
}
```

Error:

```json
{
  "jsonrpc": "2.0",
  "error": {"code": -32602, "message": "Parámetros inválidos"},
  "id": 1
}
```

Implementación mínima en Flask:

```python
@app.post("/rpc")
def rpc():
    req = request.get_json()
    if req.get("jsonrpc") != "2.0":
        return {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": req.get("id")}, 400
    method = req.get("method")
    params = req.get("params", {})
    try:
        if method == "crearJuego":
            game = service.create_game(params["jugador"], params["numero"])
            result = {"id": game.id, "estado": game.status.value}
        else:
            return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": req.get("id")}, 404
        return {"jsonrpc": "2.0", "result": result, "id": req.get("id")}
    except Exception as e:
        return {"jsonrpc": "2.0", "error": {"code": -32602, "message": str(e)}, "id": req.get("id")}, 400
```

### 4.4 gRPC

gRPC es un framework de RPC de Google basado en:

- **Protocol Buffers** (protobuf) para definir mensajes y serializar binario.
- **HTTP/2** para multiplexación, streaming y headers.
- **Generación de código** a partir de un `.proto`.

Ejemplo de contrato para Picas y Fijas:

```proto
syntax = "proto3";

package picas;

service JuegoService {
  rpc CrearJuego (CrearJuegoRequest) returns (JuegoReply);
  rpc Unirse (UnirseRequest) returns (JuegoReply);
  rpc Jugar (JugarRequest) returns (JugadaReply);
  rpc VerJuego (VerJuegoRequest) returns (JuegoReply);
  rpc ListarJuegos (ListarRequest) returns (ListaReply);
}

message CrearJuegoRequest {
  string jugador = 1;
  string numero = 2;
}

message UnirseRequest {
  string id = 1;
  string jugador = 2;
  string numero = 3;
}

message JugarRequest {
  string id = 1;
  string jugador = 2;
  string numero = 3;
}

message VerJuegoRequest {
  string id = 1;
  string jugador = 2;
}

message ListarRequest {}

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

message ListaReply {
  repeated JuegoReply juegos = 1;
}
```

Generar código Python:

```bash
pip install grpcio grpcio-tools
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. picas.proto
```

Servidor:

```python
import grpc
from concurrent import futures
import picas_pb2
import picas_pb2_grpc

class JuegoServicer(picas_pb2_grpc.JuegoServiceServicer):
    def CrearJuego(self, request, context):
        # validar request.numero y crear partida
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

Cliente:

```python
import grpc
import picas_pb2
import picas_pb2_grpc

with grpc.insecure_channel("localhost:50051") as channel:
    stub = picas_pb2_grpc.JuegoServiceStub(channel)
    reply = stub.CrearJuego(picas_pb2.CrearJuegoRequest(jugador="ana", numero="4271"))
    print(reply.id, reply.estado)
```

Tipos de streaming en gRPC:

- **Unary**: una petición, una respuesta.
- **Server streaming**: una petición, muchas respuestas.
- **Client streaming**: muchas peticiones, una respuesta.
- **Bidirectional**: muchas en ambos sentidos.

### 4.5 Errores, deadlines y reintentos

gRPC tiene códigos de estado propios:

| Código | Significado |
| --- | --- |
| `OK` | Éxito |
| `INVALID_ARGUMENT` | Argumentos inválidos |
| `NOT_FOUND` | Recurso no encontrado |
| `PERMISSION_DENIED` | Sin permiso |
| `UNAUTHENTICATED` | Falta autenticación |
| `DEADLINE_EXCEEDED` | Se acabó el tiempo |
| `UNAVAILABLE` | Servidor no disponible |
| `UNIMPLEMENTED` | Método no implementado |
| `INTERNAL` | Error interno |
| `RESOURCE_EXHAUSTED` | Sin recursos/rate limit |

Buenas prácticas:

- Definir **deadlines** en el cliente (`timeout=2`).
- Reintentar solo operaciones **idempotentes**.
- Usar **backoff exponencial** con jitter.
- No reintentar errores de negocio (`INVALID_ARGUMENT`, `PERMISSION_DENIED`).
- Versionar el `.proto`; no reutilizar números de campo.
- Mantener compatibilidad: campos nuevos opcionales; no borrar campos usados.
- Usar TLS en producción.
- Implementar health checking y balanceo.

### 4.6 Errores típicos en RPC

| Error | Causa | Solución |
| --- | --- | --- |
| `ModuleNotFoundError: grpc` | Falta instalar `grpcio` | `pip install grpcio grpcio-tools` |
| `UNIMPLEMENTED` | Método no implementado o nombre mal escrito | Revisar `.proto` y servidor |
| `DEADLINE_EXCEEDED` | Operación lenta o timeout muy bajo | Aumentar deadline, optimizar |
| `UNAVAILABLE` | Servidor apagado o puerto incorrecto | Revisar host/puerto, logs |
| `UNKNOWN` | Error de serialización/lógica | Revisar mensaje y tipos |
| `TypeError` en campos | Proto generado desactualizado | Regenerar código |
| El cliente no ve cambios | Versión de `.proto` distinta | Recompilar y desplegar ambos |

### 4.7 RPC en Picas y Fijas

El proyecto usa **REST**, no RPC. Es una decisión válida: la API es pública para el navegador, usa JSON y HTTP, y los recursos se modelan naturalmente.

Si se pidiera una versión RPC, el mapeo sería:

| REST | RPC |
| --- | --- |
| `POST /login` | `AuthService.Login(LoginRequest)` |
| `POST /juego` | `JuegoService.CrearJuego(CrearJuegoRequest)` |
| `PUT /juego/{id}` | `JuegoService.Unirse(UnirseRequest)` |
| `POST /juego/{id}/jugar` | `JuegoService.Jugar(JugarRequest)` |
| `GET /juego/{id}` | `JuegoService.VerJuego(VerJuegoRequest)` |
| `GET /juego` | `JuegoService.ListarJuegos(ListarRequest)` |

En una sustentación, si preguntan “¿por qué no usó RPC?”, la respuesta puede ser: porque el cliente principal es un navegador, REST/JSON es más simple y cacheable, y no se necesita el rendimiento de protobuf ni streaming. gRPC sería mejor si hubiera comunicación interna entre microservicios o muchos jugadores en tiempo real.

---

## 5. Kubernetes

### 5.1 ¿Qué es Kubernetes?

Kubernetes es un **orquestador de contenedores**. Declaras el **estado deseado** en YAML y el clúster se encarga de acercarse a ese estado:

- programa Pods en nodos,
- reinicia los que fallan,
- escala réplicas,
- actualiza versiones,
- expone servicios,
- distribuye configuración y secretos.

### 5.2 Arquitectura del clúster

**Plano de control:**

- `kube-apiserver`: punto de entrada; valida y sirve la API.
- `etcd`: base de datos clave-valor del estado del clúster.
- `kube-scheduler`: decide en qué nodo corre cada Pod.
- `kube-controller-manager`: controladores que reconcilian el estado (Deployment, Node, etc.).
- `cloud-controller-manager` (en nubes): integra con el proveedor.

**Nodos:**

- `kubelet`: agente que ejecuta y reporta Pods.
- `kube-proxy`: reglas de red para Services.
- Container runtime: containerd, CRI-O, etc.
- CNI: red de Pods.
- `kubectl`: CLI que habla con el API server usando `~/.kube/config`.

### 5.3 Objetos principales

| Objeto | Qué hace |
| --- | --- |
| **Pod** | Unidad mínima; uno o más contenedores con red/volumen compartido. Es efímero. |
| **ReplicaSet** | Mantiene N réplicas de un Pod. |
| **Deployment** | Gestiona ReplicaSets, actualizaciones y rollback. |
| **StatefulSet** | Pods con identidad y almacenamiento estable (bases de datos). |
| **DaemonSet** | Un Pod en cada nodo (agentes, logs). |
| **Job / CronJob** | Tareas que terminan / tareas programadas. |
| **Service** | IP/DNS estable y balanceo hacia Pods. |
| **Ingress** | Enrutamiento HTTP/HTTPS y TLS; requiere controlador. |
| **Namespace** | Aislamiento lógico y cuotas. |
| **ConfigMap** | Configuración no sensible. |
| **Secret** | Datos sensibles (base64, no cifrado por sí solo). |
| **PVC / StorageClass** | Almacenamiento persistente. |
| **HPA** | Escalado automático por CPU/memoria/métricas. |
| **NetworkPolicy** | Reglas de tráfico entre Pods. |

### 5.4 Anatomía de un YAML

Todo objeto tiene:

```yaml
apiVersion: apps/v1       # versión de la API
kind: Deployment          # tipo de objeto
metadata:
  name: mi-app            # nombre
  namespace: unillanos    # namespace
  labels:
    app: mi-app           # etiquetas
spec:                     # estado deseado
  ...
status:                   # estado observado (lo escribe Kubernetes)
  ...
```

#### Deployment

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

Puntos clave:

- `selector.matchLabels` debe coincidir con `template.metadata.labels`. Si no, el Deployment no encuentra sus Pods.
- `replicas` es el número deseado.
- `template` es la plantilla del Pod.
- `resources.requests` se usa para programar; `limits` para limitar.
- Si el contenedor supera el límite de memoria, puede ser `OOMKilled`.

> **Trampa de namespace:** el ejemplo de clase no incluye `metadata.namespace`, pero el Service sí está en `unillanos`. Si aplicas el Deployment sin `-n unillanos`, queda en `default` y el Service no encontrará sus Pods. Aplica todo con `kubectl apply -n unillanos -f ...` o agrega `metadata.namespace: unillanos` al Deployment.

#### Service

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

Tipos:

- **ClusterIP** (por defecto): solo dentro del clúster.
- **NodePort**: abre un puerto en cada nodo (30000–32767).
- **LoadBalancer**: IP externa del proveedor cloud.
- **ExternalName**: alias DNS a un servicio externo.

`port` ≠ `targetPort` ≠ `nodePort`:

- `port`: donde escucha el Service.
- `targetPort`: donde escucha el contenedor.
- `nodePort`: puerto expuesto en cada nodo (solo NodePort/LoadBalancer).

#### ConfigMap y Secret

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: "INFO"
```

```bash
kubectl -n unillanos create secret generic picas-auth \
  --from-literal=signing-key="$(openssl rand -hex 32)"
```

Uso como variables:

```yaml
env:
  - name: PICAS_SECRET_KEY
    valueFrom:
      secretKeyRef:
        name: picas-auth
        key: signing-key
```

- Un Secret no es “seguro” por sí solo: por defecto se guarda base64 en etcd. Hay que proteger etcd, usar RBAC y, si es necesario, cifrado en reposo.
- Si el Secret no existe, el Pod queda en `CreateContainerConfigError`.

#### Probes

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

- **Readiness**: si falla, el Pod no recibe tráfico (pero no se reinicia).
- **Liveness**: si falla, Kubernetes reinicia el contenedor.
- **Startup**: para aplicaciones lentas; evita que liveness las mate antes de arrancar.

#### Volúmenes e initContainers

```yaml
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
        git -C /source/repo fetch --depth=1 https://github.com/usuario/repo.git HEAD
        git -C /source/repo reset --hard FETCH_HEAD
    volumeMounts:
      - name: source
        mountPath: /source
```

- `emptyDir`: volumen temporal que vive mientras el Pod exista.
- `initContainer`: se ejecuta antes del contenedor principal y debe terminar con éxito.
- Los contenedores del mismo Pod comparten red y volúmenes.

#### Estrategias de despliegue

- **RollingUpdate** (por defecto): reemplaza Pods gradualmente; no hay downtime si hay réplicas y readiness.
- **Recreate**: elimina todos los Pods viejos y crea los nuevos; hay downtime. Se usa cuando no puede haber dos versiones a la vez (por ejemplo, estado en memoria o un volumen RWO).

### 5.5 Redes en Kubernetes

- Cada Pod tiene su propia IP.
- Los Pods pueden comunicarse entre sí (según CNI/NetworkPolicy).
- Un Service da una IP virtual y DNS estable: `mi-servicio`, `mi-servicio.unillanos`, `mi-servicio.unillanos.svc.cluster.local`.
- `kubectl port-forward` es para depurar, no para producción.
- Ingress expone HTTP/HTTPS con reglas de host/path; necesita un controlador (NGINX, Traefik, etc.).

### 5.6 Comandos de kubectl

```bash
# Contexto y nodos
kubectl config current-context
kubectl get nodes

# Namespaces
kubectl create namespace unillanos
kubectl get ns
kubectl get all -n unillanos

# Aplicar/eliminar
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl delete -f deployment.yaml

# Ver recursos
kubectl -n unillanos get pods -o wide
kubectl -n unillanos get deployments
kubectl -n unillanos get services
kubectl -n unillanos get endpoints
kubectl -n unillanos describe pod NOMBRE

# Logs
kubectl -n unillanos logs deployment/my-app
kubectl -n unillanos logs POD -c CONTENEDOR
kubectl -n unillanos logs POD --previous

# Entrar
kubectl -n unillanos exec -it POD -- sh

# Port-forward
kubectl -n unillanos port-forward service/mi-servicio 8080:80

# Rollout
kubectl -n unillanos rollout status deployment/my-app
kubectl -n unillanos rollout restart deployment/my-app
kubectl -n unillanos rollout undo deployment/my-app

# Escalar
kubectl -n unillanos scale deployment/my-app --replicas=3

# Eventos
kubectl -n unillanos get events --sort-by=.metadata.creationTimestamp
```

### 5.7 Diagnóstico: síntoma → causa → comando

| Síntoma | Causa frecuente | Qué revisar |
| --- | --- | --- |
| `Pending` | No hay recursos, taints, PVC, selector de nodo | `kubectl describe pod`, eventos |
| `ImagePullBackOff` | Imagen mal escrita, tag inexistente, registro privado | `describe pod`, nombre/tag, secret de registro |
| `ErrImageNeverPull` | `imagePullPolicy: Never` y la imagen no está en el nodo | Cambiar política o cargar la imagen |
| `CrashLoopBackOff` | La app falla al iniciar, comando incorrecto, falta env | `logs`, `logs --previous`, `describe` |
| `CreateContainerConfigError` | Falta ConfigMap/Secret/clave | `describe pod`, crear el recurso |
| `Init:Error` / `Init:CrashLoopBackOff` | Falló un initContainer | Logs del initContainer |
| `RunContainerError` | Comando/binario inexistente, permisos | `describe`, `logs` |
| `OOMKilled` | Límite de memoria muy bajo | Aumentar `limits.memory`, optimizar |
| `Evicted` | Presión de memoria/disco en el nodo | Eventos, recursos |
| `READY 0/1` | Readiness probe falla | Path, puerto, tiempo de arranque |
| Service sin respuesta | Selector no coincide, targetPort mal, app caída | `get endpoints`, `describe service`, logs |
| `502/503` en Ingress | Sin endpoints o app no lista | `get endpoints`, readiness |
| DNS no resuelve | Nombre/namespace incorrecto | `nslookup`, FQDN |

Flujo recomendado:

```bash
kubectl -n NS get pods
kubectl -n NS describe pod POD
kubectl -n NS logs POD
kubectl -n NS get events --sort-by=.metadata.creationTimestamp
kubectl -n NS get endpoints
```

### 5.8 Cómo se despliega Picas y Fijas

Archivos:

- `killercoda/namespace.yaml`: crea el namespace `picas-y-fijas`.
- `killercoda/deployment.yaml`: Pod con initContainer + contenedor `web`.
- `killercoda/service.yaml`: Service `ClusterIP` puerto 80 → `http` (5000).

Flujo:

1. Crear namespace.
2. Crear Secret `picas-auth` con `signing-key`.
3. Aplicar Deployment y Service.
4. Esperar rollout.
5. `port-forward` para acceder desde el navegador.

El Deployment:

- `replicas: 1` y `strategy: Recreate`: porque el estado vive en memoria; dos Pods tendrían partidas distintas.
- `emptyDir`: comparte el código clonado entre initContainer y web.
- `initContainers.download-code`: usa `alpine/git` para clonar el repo público en `/source/repo`.
- `containers.web`: `python:3.12-slim`; instala `requirements.txt` y Gunicorn; arranca `gunicorn --workers 1`.
- `readinessProbe`: `GET /` en el puerto `http`.
- `resources`: requests 250m/64Mi, limits 500m/128Mi.
- `PICAS_SECRET_KEY`: desde el Secret.

Service:

```yaml
type: ClusterIP
selector:
  app: picas-y-fijas
ports:
  - port: 80
    targetPort: http
```

Acceso:

```bash
kubectl port-forward -n picas-y-fijas service/picas-y-fijas \
  --address 0.0.0.0 8080:80
```

Limitaciones:

- Un solo worker/réplica: no hay estado compartido.
- Si el Pod se reinicia, se pierden usuarios y partidas.
- No hay persistencia, HPA, Ingress ni TLS.
- Las dependencias se instalan en cada arranque (más lento y dependiente de red).
- Las imágenes usan tags mutables (`python:3.12-slim`, `alpine/git:latest`).

### 5.9 Errores típicos en Kubernetes

| Error | Causa | Solución |
| --- | --- | --- |
| El Service no encuentra Pods | `selector` no coincide con labels | Igualar labels y selector |
| `targetPort` incorrecto | El Service apunta a un puerto que no escucha | Revisar `containerPort` y el `bind` |
| `CreateContainerConfigError` | Falta Secret/ConfigMap | Crearlo antes de aplicar |
| `CrashLoopBackOff` | App falla al arrancar | Logs, comando, env |
| `Pending` | Sin recursos/taints | Ajustar requests o nodos |
| `OOMKilled` | Límite de memoria | Subir límite |
| Readiness falla | Path/puerto/tiempo | Ajustar probe o app |
| `port-forward` se corta | Proceso terminado o Pod reiniciado | Volver a ejecutar |
| La app funciona local pero no en K8s | Escucha en `127.0.0.1` | Escuchar en `0.0.0.0` |

---

## 6. Cómo se integran los cuatro temas en Picas y Fijas

### 6.1 Flujo completo de una petición

```text
Navegador
  │  fetch POST /juego + JSON + Bearer token
  ▼
Flask (contenedor / Pod)
  │  @require_auth verifica token
  ▼
GameService
  │  crea Game, valida número, genera id
  ▼
MemoryGameRepository
  │  guarda en el diccionario en memoria
  ▼
jsonify(...) 201 + Location
  │
  ▼
Navegador actualiza la lista
```

- **API**: contrato HTTP/JSON.
- **Docker**: la app corre dentro de un contenedor con Python 3.12 y Gunicorn.
- **Kubernetes**: el contenedor se ejecuta en un Pod, detrás de un Service, con un Secret.
- **RPC**: no se usa; se eligió REST. Se podría reemplazar por gRPC si el requisito fuera comunicación interna de alto rendimiento.

### 6.2 Mapa de archivos

| Archivo | Responsabilidad | Tema |
| --- | --- | --- |
| `app/__init__.py` | Crea Flask, conecta dependencias, registra errores | API / arquitectura |
| `app/routes/*.py` | Endpoints y autenticación | API |
| `app/services/*.py` | Casos de uso y generación de IDs | API / dominio |
| `app/domain/game.py` | Reglas del juego | Dominio |
| `app/repositories/*.py` | Contratos e implementación en memoria | Estado |
| `app/templates/index.html` | Front, fetch, polling | API / front |
| `run.py` | Servidor local | API |
| `killercoda/*.yaml` | Despliegue | Kubernetes |
| `requirements.txt` | Dependencias | Docker / Python |

### 6.3 Comparación local vs Kubernetes

| Aspecto | Local (`python -m run`) | Kubernetes |
| --- | --- | --- |
| Servidor | Flask dev server | Gunicorn |
| Workers | 1, `threaded=False` | 1 worker |
| Recarga | `debug=True` | No |
| Estado | Memoria del proceso | Memoria del Pod |
| Acceso | `localhost:5000` | `port-forward` |
| Clave | `PICAS_SECRET_KEY` o aleatoria | Secret |
| Persistencia | Ninguna | Ninguna (`emptyDir` es temporal) |

---

## 7. Chuleta de comandos

### 7.1 cURL

```bash
curl -i URL
curl -s URL | jq
curl -X POST URL -H 'Content-Type: application/json' -d '{"k":"v"}'
curl -X PUT URL -H 'Authorization: Bearer TOKEN' -H 'Content-Type: application/json' -d '{"k":"v"}'
curl -X DELETE URL -H 'Authorization: Bearer TOKEN'
```

### 7.2 Docker

```bash
docker build -t imagen:tag .
docker run --rm -p 8080:3000 imagen:tag
docker run -d --name contenedor -p 8080:3000 imagen:tag
docker ps -a
docker logs -f contenedor
docker exec -it contenedor sh
docker stop contenedor
docker rm contenedor
docker images
docker rmi imagen:tag
docker compose up -d --build
docker compose down
```

### 7.3 kubectl

```bash
kubectl get nodes
kubectl get ns
kubectl get all -n NS
kubectl apply -f archivo.yaml
kubectl -n NS get pods -o wide
kubectl -n NS describe pod POD
kubectl -n NS logs POD
kubectl -n NS logs POD --previous
kubectl -n NS exec -it POD -- sh
kubectl -n NS port-forward service/SVC 8080:80
kubectl -n NS rollout status deployment/DEP
kubectl -n NS rollout restart deployment/DEP
kubectl -n NS scale deployment/DEP --replicas=3
kubectl -n NS delete pod POD
kubectl -n NS get events --sort-by=.metadata.creationTimestamp
```

---

## 8. Preguntas típicas con respuesta corta

> **Modo examen:** tapa la respuesta, contéstala en voz alta y solo después compárala. Si fallas, marca la pregunta y vuelve a la sección correspondiente.

1. **¿Qué es una API?**  
   Un contrato entre componentes que define operaciones, datos de entrada/salida y errores.

2. **¿Qué diferencia hay entre 401 y 403?**  
   401 = no autenticado o credencial inválida; 403 = autenticado pero sin permiso.

3. **¿Por qué el número se envía como string?**  
   Para conservar ceros iniciales (`"0123"`) y validar exactamente cuatro caracteres.

4. **¿Qué es REST?**  
   Un estilo arquitectónico basado en recursos, HTTP, stateless y una interfaz uniforme.

5. **¿REST o RPC?**  
   REST para APIs públicas y recursos; RPC/gRPC para comunicación interna, contratos fuertes y alto rendimiento.

6. **¿Qué es un contenedor?**  
   Una instancia aislada de una imagen que comparte el kernel del host.

7. **¿Diferencia entre imagen y contenedor?**  
   La imagen es la plantilla de solo lectura; el contenedor es la instancia en ejecución.

8. **¿Para qué sirve `EXPOSE`?**  
   Documenta el puerto; no lo publica. Para publicarlo se usa `-p`.

9. **¿Por qué la app no responde desde el host?**  
   Probablemente escucha en `127.0.0.1`; debe escuchar en `0.0.0.0`.

10. **¿Qué es un Pod?**  
    La unidad mínima de Kubernetes; uno o más contenedores con red y volúmenes compartidos.

11. **¿Qué hace un Deployment?**  
    Mantiene réplicas de un Pod y gestiona actualizaciones/rollback.

12. **¿Diferencia entre `port` y `targetPort`?**  
    `port` es el del Service; `targetPort` es el del contenedor.

13. **¿Por qué el Pod queda en `CreateContainerConfigError`?**  
    Porque falta un Secret/ConfigMap o una clave referenciada.

14. **¿Por qué el Pod queda en `CrashLoopBackOff`?**  
    Porque el proceso principal falla y Kubernetes lo reinicia; revisar logs.

15. **¿Qué es un readiness probe?**  
    Comprueba si el Pod puede recibir tráfico; si falla, se saca de los endpoints.

16. **¿Por qué el proyecto usa una réplica y un worker?**  
    Porque las partidas están en memoria; varios procesos tendrían estados distintos.

17. **¿Qué pasa si se reinicia el servidor?**  
    Se pierden usuarios y partidas; los tokens también pueden invalidarse si cambia la clave.

18. **¿Cómo se escala el proyecto?**  
    Con una base de datos o Redis compartido, varios workers/réplicas y una clave de firma común.

19. **¿Cómo se genera el ID de partida?**  
    Seis dígitos aleatorios distintos entre sí, sin cero inicial, verificando que no exista; si colisiona, se reintenta.

20. **¿Cómo se evita que un jugador vea el número del otro?**  
    `to_dict()` no incluye `_secrets`; solo se devuelven intentos, turno, estado y ganador.

---

## 9. Glosario

- **Stateless**: no guarda estado entre peticiones.
- **Idempotente**: repetir la operación no cambia el resultado final.
- **Token**: credencial firmada que identifica al usuario.
- **Marshalling**: convertir datos a un formato serializable.
- **Stub**: proxy local que representa un servicio remoto.
- **IDL**: lenguaje para definir interfaces (`.proto`).
- **Pod**: unidad mínima de Kubernetes.
- **Service**: abstracción estable para acceder a Pods.
- **Namespace**: aislamiento lógico.
- **Secret**: objeto para datos sensibles.
- **Probe**: comprobación de salud.
- **Rollout**: despliegue gradual de una nueva versión.
- **OOMKilled**: proceso terminado por exceder memoria.
- **Port-forward**: túnel local hacia un Service/Pod.
- **ClusterIP**: Service solo accesible dentro del clúster.
- **NodePort**: Service expuesto en un puerto de cada nodo.
- **Ingress**: enrutamiento HTTP/HTTPS de entrada.

---

> **Siguiente documento:** `02_apunte_parcial.md` contiene la versión condensada para llevar al parcial, plantillas de código y ejercicios prácticos resueltos. `03_sustentacion_proyecto.md` contiene el guion completo para defender Picas y Fijas.
