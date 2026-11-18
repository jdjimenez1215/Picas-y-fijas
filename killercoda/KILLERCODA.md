# Ejecutar Picas y Fijas en Killercoda

## Desplegar y abrir el juego

Abre el Playground de Kubernetes y ejecuta estos comandos **en orden** en la terminal `root@controlplane`. Si tienes un `port-forward` activo, deténlo antes con `Ctrl+C`.

```bash
git clone https://github.com/jdjimenez1215/Picas-y-fijas.git
cd Picas-y-fijas
kubectl apply -f killercoda/namespace.yaml
kubectl apply -f killercoda/
kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=300s
kubectl -n picas-y-fijas port-forward --address 0.0.0.0 service/picas-y-fijas 8080:80
```

Cuando veas `Forwarding from 0.0.0.0:8080`, abre **Traffic / Ports → 8080**. Usa el mismo enlace en dos pestañas y entra con nombres diferentes, por ejemplo `ana` y `luis`.

> **¿Por qué el namespace va primero?** `kubectl apply -f killercoda/` procesa los archivos en orden alfabético: `deployment.yaml` antes que `namespace.yaml`. Si el namespace no existe, el Deployment falla con `namespaces "picas-y-fijas" not found`. Al crear el namespace antes con `kubectl apply -f killercoda/namespace.yaml`, el bloque funciona.

> **Ya no hace falta crear el Secret.** El `deployment.yaml` ya no referencia `picas-auth`. Si no hay `PICAS_SECRET_KEY`, `create_app()` genera una clave aleatoria al arrancar. El login sigue funcionando; al reiniciar el Pod los tokens se invalidan (las partidas también se borran, porque están en memoria).

### Si el `port-forward` dice `pod is not running. Current status=Pending`

El túnel solo funciona cuando el Pod está `Running`. Espera al `rollout status` o verifica:

```bash
kubectl -n picas-y-fijas get pods -o wide
kubectl -n picas-y-fijas describe pod -l app=picas-y-fijas
```

## Comprobar el juego

En otra terminal (botón `+`), con el reenvío activo:

```bash
# Página HTML. Debe responder 200.
curl -i http://localhost:8080/

# Login. Debe responder 200 con un token.
curl -i http://localhost:8080/login -H 'Content-Type: application/json' -d '{"username":"ana"}'

# Estado de los recursos. El Pod debe estar READY 1/1.
kubectl get all -n picas-y-fijas

# Service ClusterIP: puerto 80 -> contenedor 5000.
kubectl -n picas-y-fijas get svc picas-y-fijas
```

## Actualizar después de un `git push`

Publica los cambios en la rama principal de GitHub y repite:

```bash
(
set -e
cd /root/Picas-y-fijas
git pull --ff-only
kubectl apply -f killercoda/namespace.yaml
kubectl apply -f killercoda/
kubectl -n picas-y-fijas rollout restart deployment/picas-y-fijas
kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=300s
)
```

El Pod vuelve a clonar el código y reinstala las dependencias. El reinicio borra las partidas en memoria.

## Actualización automática de la interfaz

- **Sala:** `startLobbyPolling()` en `app/templates/index.html` programa `refreshLobby()`, que envía `GET /juego` cada 2 segundos.
- **Partida:** `startPolling()` programa `refreshRound()`, que envía `GET /juego/{id}` cada 2 segundos.

`api()` ejecuta ambos GET con el token Bearer. Las consultas automáticas se omiten si la pestaña está oculta.

## Diagnóstico

```bash
# Muestra si el Pod está en ejecución y listo (READY 1/1).
kubectl -n picas-y-fijas get pods -o wide

# Configuración, estado y eventos de los Pods.
kubectl -n picas-y-fijas describe pod -l app=picas-y-fijas

# Mensajes del contenedor que descarga el código.
kubectl -n picas-y-fijas logs deployment/picas-y-fijas -c download-code

# Mensajes del contenedor que instala dependencias y arranca Gunicorn.
kubectl -n picas-y-fijas logs deployment/picas-y-fijas -c web

# Últimos eventos del namespace.
kubectl -n picas-y-fijas get events --sort-by=.metadata.creationTimestamp
```

| Síntoma | Causa probable | Qué hacer |
| --- | --- | --- |
| `namespaces "picas-y-fijas" not found` | Se aplicó la carpeta sin crear antes el namespace | `kubectl apply -f killercoda/namespace.yaml` y repetir |
| `error: unable to forward port because pod is not running` | El Pod está `Pending` o `ContainerCreating` | Esperar al `rollout status` y revisar `describe pod` |
| `Init:Error` / `Init:CrashLoopBackOff` | Falló el clone de GitHub | Ver logs de `-c download-code` |
| `ImagePullBackOff` | No se pudo descargar `python:3.12-slim` o `alpine/git` | Ver eventos y esperar |
| `CrashLoopBackOff` | Falló `pip install` o Gunicorn | Ver logs de `-c web` |
| `READY 0/1` | La readiness probe `GET /` aún no responde | Esperar; si persiste, ver logs de `-c web` |
| `CreateContainerConfigError` | Quedó un YAML antiguo que referencia el Secret `picas-auth` | Actualizar el repo con `git pull` y volver a aplicar |
| La página no abre | `port-forward` detenido o puerto 8080 equivocado | Repetir el `port-forward` y abrir Traffic / Ports → 8080 |

El Service es `ClusterIP` y recibe en el puerto `80`; redirige al puerto nombrado `http`, que corresponde al `5000` del contenedor. El namespace de los recursos es `picas-y-fijas`. Se usa una réplica y un worker porque los datos están en memoria: reiniciar el Pod borra usuarios y partidas.
