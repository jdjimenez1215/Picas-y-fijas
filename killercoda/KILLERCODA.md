# Picas y Fijas desde root@controlplane en Killercoda

Sigue estos pasos en la terminal del Playground Kubernetes donde aparece `root@controlplane`. Copia únicamente los comandos de cada bloque, sin incluir el texto del prompt.

Construirás la imagen del `Dockerfile` con Podman dentro de Killercoda y la cargarás en containerd, que utiliza Kubernetes. El código debe estar publicado en GitHub. La construcción descarga la imagen base de Python y las dependencias de la aplicación desde Internet.

## 1. Comprobar el clúster y descargar el proyecto

```bash
hostname
kubectl wait --for=condition=Ready nodes --all --timeout=180s
kubectl get nodes -o wide

git clone https://github.com/jdjimenez1215/Picas-y-fijas.git
cd Picas-y-fijas
ls Dockerfile killercoda/deployment.yaml killercoda/service.yaml killercoda/namespace.yaml
git log -1 --oneline
```

Si ya tienes el proyecto clonado, entra a su carpeta y ejecuta `git pull --ff-only` en lugar de clonarlo otra vez. Comprueba que el commit incluya los cambios que quieres desplegar y la carpeta `killercoda`.

## 2. Preparar Podman en controlplane

Ejecuta como `root` en la misma terminal de Killercoda.

```bash
apt-get update
apt-get install -y podman
podman --version
ctr --address /run/containerd/containerd.sock version
```

La última orden debe mostrar las versiones del cliente y del servidor containerd. Continúa cuando todos los comandos terminen correctamente.

## 3. Construir y cargar la imagen local

Desde la raíz del proyecto, define el nombre de imagen y construye usando el `Dockerfile` existente.

```bash
IMAGE=localhost/picas-y-fijas:1.0

podman build --format docker -t "$IMAGE" .
podman save --format docker-archive -o /tmp/picas-y-fijas.tar "$IMAGE"
ctr --address /run/containerd/containerd.sock --namespace k8s.io \
  images import /tmp/picas-y-fijas.tar
ctr --address /run/containerd/containerd.sock --namespace k8s.io \
  images list | grep -F "$IMAGE"
```

Si Podman pregunta de qué registro descargar `python:3.12-slim`, elige `docker.io/library/python:3.12-slim`. Esta descarga proporciona la imagen base de Python.

Comprueba que la última orden muestre `localhost/picas-y-fijas:1.0`. La importación debe hacerse en el namespace de containerd `k8s.io`, donde Kubernetes busca las imágenes. Este namespace de containerd es independiente del namespace Kubernetes `picas-y-fijas`.

## 4. Crear el namespace y la clave de autenticación

```bash
kubectl apply -f killercoda/namespace.yaml

if ! kubectl -n picas-y-fijas get secret picas-auth >/dev/null 2>&1; then
  kubectl -n picas-y-fijas create secret generic picas-auth \
    --from-literal=signing-key="$(openssl rand -hex 32)"
fi
```

El Secret proporciona la clave con la que la aplicación firma los tokens de los jugadores.

## 5. Desplegar usando la imagen de controlplane

La imagen está almacenada en `controlplane`. El siguiente ajuste dirige el Pod a ese nodo y configura `imagePullPolicy: Never` para utilizar la imagen importada. También permite ejecutar este Pod si el nodo tiene la restricción habitual de control plane.

Ejecuta todo el bloque en la misma terminal, conservando la variable `IMAGE` del paso 3.

```bash
NODE_HOSTNAME=$(kubectl get node "$(hostname)" \
  -o jsonpath='{.metadata.labels.kubernetes\.io/hostname}')

cat > /tmp/picas-local-patch.yaml <<EOF
spec:
  template:
    spec:
      nodeSelector:
        kubernetes.io/hostname: "$NODE_HOSTNAME"
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
        - key: node-role.kubernetes.io/master
          operator: Exists
          effect: NoSchedule
      containers:
        - name: web
          image: "$IMAGE"
          imagePullPolicy: Never
EOF

kubectl patch --local -f killercoda/deployment.yaml \
  --type strategic --patch-file /tmp/picas-local-patch.yaml \
  -o yaml | kubectl apply -f -
kubectl apply -f killercoda/service.yaml

kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=180s
kubectl -n picas-y-fijas get pods -o wide
kubectl -n picas-y-fijas get service
```

El Pod debe aparecer `Running`, con `READY 1/1` y `NODE controlplane`. El ajuste del Deployment se genera en `/tmp` y se aplica al clúster. Para volver a aplicarlo, utiliza este bloque completo.

## 6. Abrir el juego en el navegador

```bash
kubectl -n picas-y-fijas port-forward \
  --address 0.0.0.0 service/picas-y-fijas 8080:80
```

Mantén este comando ejecutándose. En Killercoda abre **Traffic / Ports**, introduce `8080` y abre el enlace generado. Abre ese mismo enlace en dos pestañas y entra con nombres distintos para jugar.

En otra terminal del mismo entorno puedes comprobar la respuesta de la aplicación.

```bash
curl -i http://localhost:8080/
curl -i http://localhost:8080/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"ana"}'
```

La página y el login deben responder con HTTP `200`. El login devuelve un token JSON. Para Postman puedes importar `postman/Picas-y-Fijas.postman_collection.json` y configurar su URL base con el enlace generado por Killercoda.

## 7. Actualizar la aplicación

Sube primero los cambios a GitHub. En la carpeta del proyecto, en `controlplane`, usa una etiqueta nueva y vuelve a cargar la imagen.

```bash
git pull --ff-only
IMAGE=localhost/picas-y-fijas:1.1
podman build --format docker -t "$IMAGE" .
podman save --format docker-archive -o /tmp/picas-y-fijas.tar "$IMAGE"
ctr --address /run/containerd/containerd.sock --namespace k8s.io \
  images import /tmp/picas-y-fijas.tar

kubectl -n picas-y-fijas set image deployment/picas-y-fijas web="$IMAGE"
kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=180s
```

Si el reenvío de puerto se interrumpe al reemplazarse el Pod, ejecuta otra vez el comando del paso 6. Utiliza una etiqueta nueva para cada actualización posterior.

## Diagnóstico

Ejecuta las siguientes comprobaciones desde otra terminal del mismo entorno mientras el reenvío de puerto está activo.

```bash
kubectl -n picas-y-fijas get pods -o wide
kubectl -n picas-y-fijas describe pods
kubectl -n picas-y-fijas logs deployment/picas-y-fijas
kubectl -n picas-y-fijas get events --sort-by=.metadata.creationTimestamp
ctr --address /run/containerd/containerd.sock --namespace k8s.io images list
```

- **ErrImageNeverPull**. Comprueba que el nombre y la etiqueta coincidan con la imagen importada en `k8s.io` y que el Pod se asigne a `controlplane`. Repite la importación del paso 3 y el despliegue del paso 5 con la misma variable `IMAGE`.
- **ImagePullBackOff**. Comprueba que hayas aplicado el ajuste del paso 5, que configura `imagePullPolicy: Never` para el contenedor `web`.
- **Pending**. Revisa los eventos de `describe pods`, el selector del nodo y los recursos disponibles en `controlplane`.
- **CreateContainerConfigError**. Comprueba que exista `picas-auth` en el namespace `picas-y-fijas`.
- **CrashLoopBackOff**. Revisa los logs del contenedor.
- **Página inaccesible**. Comprueba `READY 1/1`, el comando de reenvío de puerto y el enlace al puerto `8080` de esta sesión.
- **Archivo YAML inexistente**. Ejecuta `pwd` y `ls killercoda`. Debes estar en la raíz del repositorio con los archivos publicados en GitHub.

El Deployment utiliza una réplica y Gunicorn un worker porque la aplicación guarda usuarios y partidas en memoria. Reemplazar el Pod borra esos datos. Al terminar la sesión de Killercoda se pierde el entorno, incluida la imagen local. En una sesión nueva repite la guía.

## Referencias

- [Construcción de imágenes con Podman](https://docs.podman.io/en/latest/markdown/podman-build.1.html).
- [Exportación de imágenes con Podman](https://docs.podman.io/en/latest/markdown/podman-save.1.html).
- [Imágenes locales y políticas de descarga de Kubernetes](https://kubernetes.io/docs/concepts/containers/images/).
- [Reenvío de puertos en Kubernetes](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/).
