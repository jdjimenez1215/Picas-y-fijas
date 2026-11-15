# Ejecutar Picas y Fijas en Killercoda

Sigue estos pasos en el Playground Kubernetes desde la terminal `root@controlplane`. La aplicación utiliza el código público de GitHub y las imágenes públicas `alpine/git:latest` y `python:3.12-slim`.

## 1. Publicar y descargar el código

Publica en GitHub `app/`, `run.py`, `requirements.txt`, `killercoda/`, `.gitignore` y `README.md`. El Deployment obtiene la rama predeterminada de `https://github.com/jdjimenez1215/Picas-y-fijas.git`.

En la terminal de Killercoda ejecuta los siguientes comandos.

```bash
kubectl wait --for=condition=Ready nodes --all --timeout=180s
kubectl get nodes

git clone https://github.com/jdjimenez1215/Picas-y-fijas.git
cd Picas-y-fijas
ls killercoda
git log -1 --oneline
```

Si ya está clonado, entra a la carpeta y ejecuta `git pull --ff-only`.

## 2. Crear el namespace y el Secret

```bash
kubectl apply -f killercoda/namespace.yaml

if ! kubectl -n picas-y-fijas get secret picas-auth >/dev/null 2>&1; then
  kubectl -n picas-y-fijas create secret generic picas-auth \
    --from-literal=signing-key="$(openssl rand -hex 32)"
fi
```

El Secret guarda la clave usada para firmar los tokens del login. Repetir el bloque conserva el Secret existente.

## 3. Aplicar el Deployment y el Service

```bash
kubectl apply -f killercoda/deployment.yaml
kubectl apply -f killercoda/service.yaml
kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=300s
kubectl get all -n picas-y-fijas
kubectl -n picas-y-fijas get pods -o wide
```

El contenedor de inicio `download-code` descarga el código en un volumen compartido. Después `web` instala `requirements.txt` y Gunicorn e inicia el servidor en el puerto `5000`. El Pod debe aparecer `Running` con `READY 1/1`. Necesita conexión al registro de imágenes, a GitHub y a PyPI.


## 4. Abrir el juego

```bash
kubectl port-forward -n picas-y-fijas service/picas-y-fijas \
  --address 0.0.0.0 8080:80
```

Mantén este comando ejecutándose. Abre **Traffic / Ports** en Killercoda, introduce `8080` y abre el enlace generado. Usa el mismo enlace en dos pestañas y entra con nombres diferentes.

Desde otra terminal de la misma sesión puedes comprobar la aplicación.

```bash
curl -i http://localhost:8080/
curl -i http://localhost:8080/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"ana"}'
```

Ambas peticiones deben responder con HTTP `200`. El login devuelve JSON con un token. En `README.md` están todas las rutas y los cuerpos de ejemplo.

## 5. Actualizar la aplicación

Publica primero los cambios en la rama predeterminada de GitHub. En la carpeta del proyecto de Killercoda ejecuta lo siguiente.

```bash
git pull --ff-only
kubectl apply -f killercoda/deployment.yaml
kubectl apply -f killercoda/service.yaml
kubectl -n picas-y-fijas rollout restart deployment/picas-y-fijas
kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=300s
```

El nuevo Pod vuelve a descargar el código y las dependencias. Si termina el reenvío de puerto, ejecuta nuevamente el comando del paso 4.

## Diagnóstico

```bash
kubectl -n picas-y-fijas get pods -o wide
kubectl -n picas-y-fijas describe pods
kubectl -n picas-y-fijas logs deployment/picas-y-fijas -c download-code
kubectl -n picas-y-fijas logs deployment/picas-y-fijas -c web
kubectl -n picas-y-fijas get events --sort-by=.metadata.creationTimestamp
```

| Síntoma | Comprobación |
| --- | --- |
| `Init:Error` o `Init:CrashLoopBackOff` | Logs de `download-code` y acceso al repositorio público |
| `ImagePullBackOff` | Eventos del Pod y descarga de las imágenes públicas |
| `ErrImageNeverPull` | El YAML actualizado debe usar `python:3.12-slim` y `IfNotPresent` |
| `CreateContainerConfigError` | Secret `picas-auth` y clave `signing-key` en el namespace correcto |
| `CrashLoopBackOff` | Logs de `web`, instalación de paquetes y arranque de Gunicorn |
| `Pending` | Eventos, recursos de los nodos y selectores antiguos |
| Página inaccesible | Pod `READY 1/1`, reenvío activo y enlace al puerto `8080` |

El Service `ClusterIP` recibe en `80` y dirige al puerto nombrado `http`, que corresponde a `5000`. El namespace del Deployment, el Service y el Secret es `picas-y-fijas`.

Se utiliza una réplica y un worker porque los datos están en memoria. Reiniciar el proceso o reemplazar el Pod borra las partidas. Al terminar la sesión de Killercoda se pierde el entorno y debe repetirse la guía en la siguiente sesión.

Las imágenes se descargan desde un registro público. Tu cuenta de Docker Hub y una imagen propia son opcionales para este procedimiento. El contenedor prepara la aplicación durante el arranque.
