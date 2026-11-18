# Ejecutar Picas y Fijas en Killercoda

## Desplegar y abrir el juego

Pega el bloque completo en la terminal `root@controlplane`. Si tienes un reenvío abierto, detenlo primero con `Ctrl+C`.

```bash
(
# Detiene el bloque si falla un comando.
set -e
# Va a la carpeta desde la que se descarga el proyecto.
cd /root
# Actualiza la copia existente o clona el repositorio.
if [ -d Picas-y-fijas/.git ]; then
  git -C Picas-y-fijas pull --ff-only
else
  git clone https://github.com/jdjimenez1215/Picas-y-fijas.git
fi
# Entra a la carpeta que contiene los YAML.
cd Picas-y-fijas

# Espera hasta 180 segundos a que los nodos estén listos.
kubectl wait --for=condition=Ready nodes --all --timeout=180s
# Crea el namespace picas-y-fijas para agrupar los recursos.
kubectl apply -f killercoda/namespace.yaml
# Si no existe el Secret, genera una clave aleatoria para firmar los tokens.
if ! kubectl -n picas-y-fijas get secret picas-auth >/dev/null 2>&1; then
  kubectl -n picas-y-fijas create secret generic picas-auth --from-literal=signing-key="$(openssl rand -hex 32)"
fi

# Aplica el Deployment que arranca el Pod de Flask.
kubectl apply -f killercoda/deployment.yaml
# Crea o actualiza el Service que conecta el puerto 80 con el 5000 del Pod.
kubectl apply -f killercoda/service.yaml
# Recrea el Pod para descargar el código publicado en GitHub.
kubectl -n picas-y-fijas rollout restart deployment/picas-y-fijas
# Espera hasta 300 segundos a que el Deployment esté listo.
kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=300s
# Escucha en todas las interfaces y reenvía el puerto 8080 al 80 del Service.
kubectl -n picas-y-fijas port-forward --address 0.0.0.0 service/picas-y-fijas 8080:80
)
```

Deja el último comando activo y abre **Traffic / Ports → 8080**. Para actualizar, publica primero los cambios en la rama predeterminada de GitHub y repite el bloque. El reinicio borra las partidas en memoria.

## Comprobar el juego

En otra terminal, con el reenvío activo:

```bash
# Solicita la página y muestra el código HTTP.
curl -i http://localhost:8080/
# Envía el nombre como JSON a /login y recibe un token.
curl -i http://localhost:8080/login -H 'Content-Type: application/json' -d '{"username":"ana"}'
```

## Actualización automática

- **Sala:** [`startLobbyPolling()`](../app/templates/index.html#L138) programa [`refreshLobby()`](../app/templates/index.html#L143), que envía `GET /juego` cada 2 segundos.
- **Partida:** [`startPolling()`](../app/templates/index.html#L122) programa [`refreshRound()`](../app/templates/index.html#L127), que envía `GET /juego/{id}` cada 2 segundos.

[`api()`](../app/templates/index.html#L88) ejecuta ambos GET con el token Bearer. Las consultas automáticas se omiten si la pestaña está oculta.

## Diagnóstico

```bash
# Muestra si el Pod está en ejecución y listo (READY 1/1).
kubectl -n picas-y-fijas get pods -o wide
# Muestra la configuración, el estado y los eventos de los Pods.
kubectl -n picas-y-fijas describe pods
# Muestra los mensajes del contenedor que descarga el código.
kubectl -n picas-y-fijas logs deployment/picas-y-fijas -c download-code
# Muestra los mensajes del contenedor que instala dependencias y arranca Gunicorn.
kubectl -n picas-y-fijas logs deployment/picas-y-fijas -c web
# Lista los eventos del namespace del más antiguo al más reciente.
kubectl -n picas-y-fijas get events --sort-by=.metadata.creationTimestamp
```

Si aparece `CreateContainerConfigError`, revisa que el Secret `picas-auth` tenga la clave `signing-key`. Si el Pod está listo pero la página no abre, comprueba que el reenvío siga activo en `8080`.
