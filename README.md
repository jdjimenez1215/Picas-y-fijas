# Picas y Fijas

Juego de dos jugadores con interfaz web y API REST en Flask. Cada jugador elige cuatro dígitos distintos. El servidor sortea el primer turno cuando se une el segundo jugador. Gana quien consigue cuatro fijas.

## Ejecutar en Windows

Desde la raíz del proyecto, con Python 3.12 instalado, ejecuta en PowerShell.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m run
```

Abre `http://localhost:5000` en dos pestañas. Entra como `ana` y `luis`, crea una partida y une al segundo jugador. El listado de partidas y la partida se actualizan automáticamente cada pocos segundos, así que no hace falta pulsar ningún botón para ver nuevas partidas, el turno o las jugadas del rival. Al terminar se muestra el ganador y puedes volver a la sala. **Cerrar sesión** permite ingresar con otro nombre.

Para detener el servidor pulsa `Ctrl+C`. Para volver a iniciarlo basta con el último comando. El servidor local utiliza el modo de desarrollo y recarga al guardar cambios.

En Linux o macOS utiliza `.venv/bin/python` en lugar de `.\.venv\Scripts\python.exe`.

## Ejecutar en Killercoda

Abre el Playground de Kubernetes y ejecuta estos comandos **en orden** en la terminal `root@controlplane`. Si tienes un reenvío activo, deténlo con `Ctrl+C` primero.

```bash
git clone https://github.com/jdjimenez1215/Picas-y-fijas.git
cd Picas-y-fijas
kubectl apply -f killercoda/namespace.yaml
kubectl apply -f killercoda/
kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=300s
kubectl -n picas-y-fijas port-forward --address 0.0.0.0 service/picas-y-fijas 8080:80
```

Cuando veas `Forwarding from 0.0.0.0:8080`, deja la terminal abierta y entra por **Traffic / Ports → 8080**. No hace falta crear el Secret `picas-auth`: si no hay `PICAS_SECRET_KEY`, la app genera una clave al arrancar. Para revisar fallos, consulta [la guía de Killercoda](killercoda/KILLERCODA.md#diagnóstico).

## API

Envía los cuerpos JSON con `Content-Type: application/json`. Todas las operaciones de `/juego` requieren `Authorization: Bearer TOKEN`.

| Método | Ruta | Cuerpo JSON | Respuesta exitosa |
| --- | --- | --- | --- |
| GET | `/` | — | 200, página HTML |
| POST | `/login` | `{"username":"ana"}` | 200, token firmado |
| POST | `/juego` | `{"number":"4271"}` | 201, partida creada |
| PUT | `/juego/{id}` | `{"username":"luis","number":"0123"}` | 200, partida con dos jugadores |
| POST | `/juego/{id}/jugar` | `{"number":"0134"}` | 200, intento con picas y fijas |
| GET | `/juego/{id}` | — | 200, estado completo para participantes |
| GET | `/juego` | — | 200, resumen de todas las partidas |

`number` es texto para conservar ceros iniciales. Debe contener exactamente cuatro dígitos ASCII diferentes. El identificador de cada partida (`id`) es un número de seis dígitos distintos, generado al azar y único. El usuario del cuerpo de la petición para unirse debe coincidir con el del token. El resultado de jugar contiene `player`, `guess`, `fijas` y `picas`. Consulta después `GET /juego/{id}` para obtener el turno, el estado y el ganador.

Los estados son `waiting`, `in_progress` y `finished`. Los errores se devuelven como JSON con `error`. Los códigos principales son 400 para entradas o transiciones inválidas, 401 para token ausente, inválido o vencido, 403 para acceso o turno denegados, 404 para una partida inexistente, 405 para un método HTTP no admitido y 415 para un cuerpo enviado con tipo de contenido incorrecto.

## Archivos para GitHub

Publica `app/`, `run.py`, `requirements.txt`, `killercoda/`, `.gitignore` y este `README.md`. El repositorio público utilizado por el Deployment es `https://github.com/jdjimenez1215/Picas-y-fijas.git` y el Pod obtiene su rama predeterminada.

El entorno `.venv/` y las cachés se generan localmente y están excluidos por `.gitignore`. La clave `PICAS_SECRET_KEY` se configura en ejecución. El Secret de Kubernetes se crea desde la terminal.

## Organización y límites de la demostración

- `app/domain` contiene las reglas y los modelos del juego.
- `app/services` coordina autenticación y partidas.
- `app/repositories` define los contratos de almacenamiento y sus implementaciones en memoria.
- `app/routes` expone las operaciones HTTP y verifica los tokens.
- `app/templates/index.html` contiene la interfaz y las peticiones del navegador.
- `app/__init__.py` crea Flask, conecta servicios y registra las rutas y errores.

En `docs/` hay material de apoyo para el corte: [código explicado archivo por archivo](docs/04_codigo_explicado.md), [teoría de API, Docker, RPC y Kubernetes](docs/01_teoria_api_docker_rpc_kubernetes.md), [apunte de ejercicios](docs/02_apunte_parcial.md) y [guion de sustentación](docs/03_sustentacion_proyecto.md).

El almacenamiento vive en la memoria de un proceso. Reiniciarlo borra usuarios y partidas. Se utiliza una réplica y un worker para compartir ese estado entre los jugadores. El login identifica por nombre y genera tokens firmados con una vigencia de una hora. Cerrar sesión elimina el token de la pestaña. Un token ya copiado mantiene su validez hasta vencer o cambiar la clave de firma.
