# Desplegar Picas y Fijas en Killercoda

## 1. Publicar el código y la imagen desde Windows

Guarda y sube a GitHub los cambios del proyecto, incluidos Dockerfile y la carpeta k8s. El repositorio configurado es https://github.com/jdjimenez1215/Picas-y-fijas.git. Comprueba que los últimos cambios estén publicados antes de clonarlo en Killercoda.

Abre Docker Desktop y, desde CMD en la raíz del proyecto, reemplaza TU_USUARIO_DOCKERHUB por tu usuario real de Docker Hub:

```bat
cd /d "D:\taller distri\Picas-y-fijas"
docker login
docker build --platform linux/amd64 -t TU_USUARIO_DOCKERHUB/picas-y-fijas:1.1 .
docker push TU_USUARIO_DOCKERHUB/picas-y-fijas:1.1
```

El repositorio de imagen debe ser público para seguir estos pasos sin configurar credenciales de descarga en Kubernetes. El usuario de Docker Hub no tiene por qué coincidir con el de GitHub.

## 2. Preparar Killercoda

Abre https://killercoda.com/playgrounds/scenario/kubernetes. Los siguientes comandos son para su terminal Linux, no para CMD de Windows:

```bash
kubectl get nodes
git clone https://github.com/jdjimenez1215/Picas-y-fijas.git
cd Picas-y-fijas
```

Espera a que los nodos estén Ready. Si ya clonaste el repositorio en esa sesión, entra a la carpeta y usa `git pull` en lugar de volver a clonarlo.

## 3. Crear los recursos

Sustituye el usuario en IMAGE por el mismo que usaste al publicar la imagen:

```bash
IMAGE=TU_USUARIO_DOCKERHUB/picas-y-fijas:1.1

kubectl apply -f k8s/namespace.yaml

kubectl -n picas-y-fijas create secret generic picas-auth \
  --from-literal=signing-key="$(openssl rand -hex 32)" \
  --dry-run=client -o yaml | kubectl apply -f -

sed "s|image: picas-y-fijas:1.0|image: $IMAGE|" k8s/deployment.yaml | kubectl apply -f -
kubectl apply -f k8s/service.yaml

kubectl -n picas-y-fijas rollout status deployment/picas-y-fijas --timeout=180s
kubectl -n picas-y-fijas get all
```

`sed` sustituye la imagen del manifiesto al enviarlo a Kubernetes. No modifica el archivo. Para futuros despliegues publica una etiqueta nueva y actualiza IMAGE. Si vuelves a ejecutar el paso del Secret, la clave cambia; los tokens emitidos con la clave anterior dejarán de funcionar cuando el proceso cargue la nueva clave.

## 4. Abrir la aplicación

```bash
kubectl -n picas-y-fijas port-forward \
  --address 0.0.0.0 service/picas-y-fijas 8080:80
```

Deja el comando ejecutándose. Abre Traffic / Ports en Killercoda, introduce 8080 y abre el enlace generado. Desde otra terminal de la misma sesión puedes comprobar:

```bash
curl -i http://localhost:8080/
curl -i http://localhost:8080/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"ana"}'
```

La primera petición debe devolver 200 con HTML y la segunda 200 con un token JSON. En Postman configura baseUrl con la URL generada por Killercoda, sin la barra final, e importa la colección de la carpeta postman.

## Diferencias respecto al ejemplo del profesor

- Imagen: la de Picas y Fijas publicada en Docker Hub, en lugar de nginx.
- Namespace: picas-y-fijas en Namespace, Deployment y Service.
- Puerto: el Service recibe en 80 y envía al puerto nombrado http, que corresponde al 5000 del contenedor.
- Una réplica y un worker: los datos están en memoria. Tres réplicas tendrían listas distintas; hace falta almacenamiento compartido antes de escalar.
- El Secret picas-auth suministra la clave de firma de tokens.
- Aplica el Service del archivo; no hace falta crear otro con kubectl expose.

El servicio es ClusterIP por defecto. Port-forward proporciona acceso desde el host del entorno. Si se interrumpe el comando o termina la sesión de Killercoda, el enlace deja de servir la aplicación. Reiniciar el Pod borra las partidas almacenadas en memoria.

## Diagnóstico

```bash
kubectl -n picas-y-fijas get pods
kubectl -n picas-y-fijas describe pods
kubectl -n picas-y-fijas logs deployment/picas-y-fijas
kubectl -n picas-y-fijas get events --sort-by=.metadata.creationTimestamp
```

- ImagePullBackOff: revisa usuario, etiqueta, publicación e imagen pública en Docker Hub.
- CreateContainerConfigError: comprueba que exista el Secret picas-auth en picas-y-fijas.
- CrashLoopBackOff: revisa los logs del contenedor.
- Página inaccesible: verifica Pod Ready 1/1, port-forward activo y puerto 8080 en Traffic / Ports.

Referencias: https://killercoda.com/creators y https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/
