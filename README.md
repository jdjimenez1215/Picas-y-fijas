# Picas y Fijas

Juego para dos jugadores con API REST en Flask, interfaz web y despliegue en Kubernetes. Cada jugador elige un número de cuatro dígitos distintos. Al unirse el segundo jugador, el servidor elige al azar quién empieza. Luego alternan turnos e intentan adivinar el número del otro. Gana quien obtiene cuatro fijas.

## Ejecutar localmente

Con Python 3.12, desde la raíz del repositorio:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m run
```

En PowerShell, activa el entorno con `.\.venv\Scripts\Activate.ps1`. Abre **http://localhost:5000** en dos pestañas. Entra como `ana` en una y `luis` en la otra. Ana crea una partida con `4271`. Luis actualiza la lista, elige la partida y se une con `0123`. Pulsa **Ver partida** en cada pestaña para consultar el turno actual.

## API REST

Las cinco operaciones de juego requieren `Authorization: Bearer <token>`. Envía los cuerpos con `Content-Type: application/json`. El campo `number` es una cadena de cuatro dígitos distintos, así que valores como `"0123"` conservan el cero inicial.

| Método y ruta | Cuerpo de ejemplo | Respuesta |
| --- | --- | --- |
| `POST /login` | `{"username":"ana"}` | 200 y token firmado |
| `POST /juego` | `{"number":"4271"}` | 201 y partida en espera |
| `PUT /juego/{id}` | `{"username":"luis","number":"0123"}` | 200 y partida en juego con su primer turno |
| `POST /juego/{id}/jugar` | `{"number":"1234"}` | 200 con intento, jugador, picas y fijas |
| `GET /juego/{id}` | | 200 con estado, creador, jugadores, turno, intentos y ganador |
| `GET /juego` | | 200 con la lista de partidas de todos los estados |

El usuario enviado al unirse debe coincidir con el usuario del token. Los estados son `waiting`, `in_progress` y `finished`. Los errores regresan JSON. Un token faltante o inválido da 401. Jugar fuera de turno o sin pertenecer a la partida da 403. Una partida inexistente da 404. Los números inválidos y las transiciones inválidas dan 400.

```bash
BASE=http://localhost:5000
ANA=$(curl -fsS "$BASE/login" -H 'Content-Type: application/json' -d '{"username":"ana"}' | python -c 'import json,sys; print(json.load(sys.stdin)["token"])')
LUIS=$(curl -fsS "$BASE/login" -H 'Content-Type: application/json' -d '{"username":"luis"}' | python -c 'import json,sys; print(json.load(sys.stdin)["token"])')
ID=$(curl -fsS "$BASE/juego" -H "Authorization: Bearer $ANA" -H 'Content-Type: application/json' -d '{"number":"4271"}' | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl -fsS -X PUT "$BASE/juego/$ID" -H "Authorization: Bearer $LUIS" -H 'Content-Type: application/json' -d '{"username":"luis","number":"0123"}'
curl -fsS "$BASE/juego/$ID" -H "Authorization: Bearer $ANA"
curl -fsS "$BASE/juego" -H "Authorization: Bearer $ANA"
```

Lee `turn` antes de enviar un intento. Si empieza Luis, ejecuta:

```bash
curl -fsS "$BASE/juego/$ID/jugar" -H "Authorization: Bearer $LUIS" -H 'Content-Type: application/json' -d '{"number":"1234"}'
```

Eso devuelve una fija y dos picas contra `4271`. Si empieza Ana, usa el token `$ANA` y prueba `"0134"` contra `0123`.

## Docker

```bash
docker build -t picas-y-fijas:1.0 .
docker run --rm -p 5000:5000 -e PICAS_SECRET_KEY="$(openssl rand -hex 32)" picas-y-fijas:1.0
```

## Kubernetes

Construye la imagen como en el paso anterior. Hazla disponible para todos los nodos donde pueda arrancar el pod. Con kind usa `kind load docker-image picas-y-fijas:1.0`. Con Minikube usa `minikube image load picas-y-fijas:1.0`. Para un clúster remoto como Killercoda, publica la imagen en un registro accesible y cambia `image` en `k8s/deployment.yaml` por el nombre completo de esa imagen con su etiqueta.

```bash
kubectl apply -f k8s/namespace.yaml
kubectl -n picas-y-fijas create secret generic picas-auth \
  --from-literal=signing-key="$(openssl rand -hex 32)" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas
kubectl -n picas-y-fijas port-forward service/picas-y-fijas 8080:80
```

Abre **http://localhost:8080**. En Killercoda usa la vista del puerto 8080 de su interfaz y añade `--address 0.0.0.0` al comando de port-forward.

El Service ClusterIP dirige el puerto 80 al puerto 5000 del contenedor. Se usa una sola réplica y un solo worker porque el repositorio vive en memoria del proceso. Al reiniciar el proceso se pierden las partidas. Para sostener varias réplicas o conservar partidas entre reinicios se necesita un repositorio compartido. El login por nombre es para la demostración y permite que cualquiera que conozca un nombre actúe como ese jugador. Los tokens vencen después de una hora.

## Código

- `app/domain` contiene las reglas del juego.
- `app/services` coordina el dominio y los repositorios.
- `app/repositories` conserva usuarios y partidas en memoria.
- `app/routes` publica la API y aplica el decorador de autenticación.
- `app/__init__.py` ensambla las dependencias y registra las rutas.
