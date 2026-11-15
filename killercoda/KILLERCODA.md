# Desplegar Picas y Fijas con kubectl en Killercoda

Ejecuta los siguientes bloques desde la terminal `root@controlplane` del Playground Kubernetes. Copia los comandos sin incluir el texto del prompt.

El Deployment descarga el código público de GitHub con un contenedor de inicio `alpine/git`. Después el contenedor `python:3.12-slim` instala las dependencias y ejecuta el juego con Gunicorn. Kubernetes descarga automáticamente esas imágenes públicas. Puedes realizar el despliegue con Git y kubectl, sin instalar Podman, abrir Docker Desktop o publicar una imagen propia.

## 1. Publicar los cambios y descargar el proyecto

Sube a GitHub los cambios de la aplicación y los archivos de `killercoda`, incluido el Deployment actualizado. El Pod descargará la rama predeterminada del repositorio público.

En Killercoda ejecuta lo siguiente.

```bash
kubectl wait --for=condition=Ready nodes --all --timeout=180s
kubectl get nodes

git clone https://github.com/jdjimenez1215/Picas-y-fijas.git
cd Picas-y-fijas
ls killercoda
git log -1 --oneline
```

Si ya clonaste el repositorio, entra a su carpeta y ejecuta `git pull --ff-only` para obtener los cambios.

## 2. Crear el namespace y la clave de autenticación

```bash
kubectl apply -f killercoda/namespace.yaml
kubectl get ns

if ! kubectl -n picas-y-fijas get secret picas-auth >/dev/null 2>&1; then
  kubectl -n picas-y-fijas create secret generic picas-auth \
    --from-literal=signing-key="$(openssl rand -hex 32)"
fi
```

El Secret proporciona la clave de firma de los tokens del login.

## 3. Aplicar el Deployment y el Service

```bash
kubectl apply -f killercoda/deployment.yaml
kubectl apply -f killercoda/service.yaml

kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=300s
kubectl get all -n picas-y-fijas
kubectl -n picas-y-fijas get pods -o wide
```

Espera a que el Pod aparezca `Running` con `READY 1/1`. El primer arranque requiere descargar las imágenes, el código y los paquetes Python. El entorno necesita acceso a GitHub, al registro de imágenes y a PyPI.

El namespace del Deployment y del Service es `picas-y-fijas`. El Service ya está definido en el archivo y se crea con `kubectl apply`.

Si habías aplicado el ajuste de la guía anterior que fijaba el Pod a `controlplane`, ejecuta este comando antes de esperar el despliegue para retirar ese selector.

```bash
kubectl -n picas-y-fijas patch deployment picas-y-fijas \
  --type merge -p '{"spec":{"template":{"spec":{"nodeSelector":null}}}}'
kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=300s
```

## 4. Abrir el juego

```bash
kubectl port-forward -n picas-y-fijas service/picas-y-fijas \
  --address 0.0.0.0 8080:80
```

Deja el comando ejecutándose. En Killercoda abre **Traffic / Ports**, introduce `8080` y abre el enlace generado. Abre el mismo enlace en dos pestañas y entra con nombres distintos para jugar.

Desde otra terminal del mismo entorno puedes comprobar la web y el login.

```bash
curl -i http://localhost:8080/
curl -i http://localhost:8080/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"ana"}'
```

Ambas peticiones deben responder HTTP `200`. El login devuelve un token JSON.

## Endpoints REST y JSON

| Método | Ruta | Operación |
| --- | --- | --- |
| POST | `/login` | Iniciar sesión |
| POST | `/juego` | Crear partida |
| PUT | `/juego/{ID}` | Unirse a una partida |
| POST | `/juego/{ID}/jugar` | Enviar un intento |
| GET | `/juego/{ID}` | Consultar el estado |
| GET | `/juego` | Listar partidas |

Las rutas `/juego` requieren el encabezado `Authorization: Bearer TOKEN`. Para enviar JSON utiliza `Content-Type: application/json`. En `README.md` están los cuerpos de ejemplo. Puedes importar `postman/Picas-y-Fijas.postman_collection.json` y configurar la URL base con el enlace generado por Killercoda.

## Actualizar el código desplegado

Después de publicar los cambios en la rama predeterminada de GitHub, ejecuta lo siguiente.

```bash
git pull --ff-only
kubectl apply -f killercoda/deployment.yaml
kubectl apply -f killercoda/service.yaml
kubectl -n picas-y-fijas rollout restart deployment/picas-y-fijas
kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=300s
```

El nuevo Pod descarga el código publicado. Si se interrumpe el reenvío de puerto, vuelve a ejecutar el comando del paso 4.

## Diferencias con el ejemplo del profesor

El ejemplo usa `nginx:1.25`, que ya contiene el servidor Nginx. Este Deployment usa una imagen de Python y descarga el código del juego desde el repositorio para ejecutar la API REST y la interfaz web.

Se utiliza una réplica y un worker porque usuarios y partidas viven en memoria del proceso. Reiniciar o reemplazar el Pod borra esos datos. Para utilizar tres réplicas con partidas compartidas hace falta un almacenamiento común.

El Service recibe en el puerto `80` y envía las peticiones al puerto `5000` de la aplicación. El enlace de Killercoda accede mediante el puerto `8080` del reenvío.

## Diagnóstico

```bash
kubectl -n picas-y-fijas get pods -o wide
kubectl -n picas-y-fijas describe pods
kubectl -n picas-y-fijas logs deployment/picas-y-fijas -c download-code
kubectl -n picas-y-fijas logs deployment/picas-y-fijas -c web
kubectl -n picas-y-fijas get events --sort-by=.metadata.creationTimestamp
```

- **Init:Error o Init:CrashLoopBackOff**. Revisa los logs de `download-code` y comprueba que el repositorio sea público y accesible desde el entorno.
- **ImagePullBackOff**. Revisa los eventos del Pod para identificar la imagen y el error de descarga. Las imágenes utilizadas son `alpine/git:latest` y `python:3.12-slim`.
- **ErrImageNeverPull**. Actualiza el archivo `killercoda/deployment.yaml` desde GitHub y vuelve a aplicarlo. El contenedor `web` debe utilizar `python:3.12-slim` con `imagePullPolicy: IfNotPresent`.
- **CreateContainerConfigError**. Comprueba que exista el Secret `picas-auth` en `picas-y-fijas`.
- **CrashLoopBackOff**. Revisa los logs de `web`, incluida la instalación de dependencias y el inicio de Gunicorn.
- **Pending**. Revisa los eventos y los recursos disponibles en los nodos.
- **Página inaccesible**. Comprueba `READY 1/1`, el reenvío activo y el enlace del puerto `8080` de esta sesión.

Al terminar la sesión de Killercoda se pierde el entorno. En una sesión nueva repite los pasos de la guía.

## Referencias

- [Contenedores de inicio de Kubernetes](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/).
- [Imagen pública alpine/git](https://github.com/alpine-docker/git).
- [Reenvío de puertos en Kubernetes](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/).
