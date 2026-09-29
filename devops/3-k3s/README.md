# DevOps 3 — Despliegue en k3s

Despliegue del Backend 4 (Django REST Framework) en un clúster k3s local usando WSL2.

---

## Requisitos previos

- WSL2 con Ubuntu instalado
- k3s instalado y el nodo en estado `Ready`:

```bash
kubectl get nodes
# NAME       STATUS   ROLES           VERSION
# madrigal   Ready    control-plane   v1.36.4+k3s1
```

- Imagen publicada en Docker Hub:
  `docker.io/juanpablomc/ihungo-backend:sha-6568187`

---

## Estructura de manifiestos

```
devops/3-k3s/manifests/
├── namespace.yaml    # Namespace ihungo
├── configmap.yaml    # Configuración no sensible
├── secret.yaml       # Placeholders — el Secret real se crea desde CLI
├── postgres.yaml     # StatefulSet + Service headless de PostgreSQL
├── deployment.yaml   # Deployment del backend con 2 réplicas
└── service.yaml      # Service NodePort 30080
```

---

## Paso 1 — Crear el namespace, ConfigMap y Secret

```bash
kubectl apply -f devops/3-k3s/manifests/namespace.yaml
kubectl apply -f devops/3-k3s/manifests/configmap.yaml
```

El `secret.yaml` versionado contiene únicamente placeholders. El Secret real se crea desde CLI con valores generados aleatoriamente:

```bash
DJANGO_SECRET_KEY=$(openssl rand -base64 48)
POSTGRES_PASSWORD=$(openssl rand -base64 32)

kubectl create secret generic ihungo-secret \
  --namespace=ihungo \
  --from-literal=DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" \
  --from-literal=POSTGRES_USER="ihungo_user" \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD"

unset DJANGO_SECRET_KEY
unset POSTGRES_PASSWORD
```

Verificar:

```bash
kubectl get secret -n ihungo
kubectl describe secret ihungo-secret -n ihungo
# Debe mostrar las 3 claves sin exponer sus valores
```

---

## Paso 2 — Desplegar PostgreSQL

```bash
kubectl apply -f devops/3-k3s/manifests/postgres.yaml
```

Esperar a que el pod esté listo:

```bash
kubectl rollout status statefulset/postgres -n ihungo
```

Verificar PVC y Service:

```bash
kubectl get pvc -n ihungo
# postgres-data-postgres-0   Bound

kubectl get svc -n ihungo
# postgres-svc   ClusterIP   None   5432/TCP
```

---

## Paso 3 — Desplegar el backend

```bash
kubectl apply -f devops/3-k3s/manifests/deployment.yaml
```

Esperar a que ambas réplicas estén listas:

```bash
kubectl rollout status deployment/ihungo-backend -n ihungo
```

Verificar pods:

```bash
kubectl get pods -n ihungo
# NAME                              READY   STATUS
# postgres-0                        1/1     Running
# ihungo-backend-xxxx-yyyy          1/1     Running
# ihungo-backend-xxxx-zzzz          1/1     Running
```

---

## Paso 4 — Exponer el Service NodePort

```bash
kubectl apply -f devops/3-k3s/manifests/service.yaml
```

Verificar:

```bash
kubectl get svc -n ihungo
# ihungo-backend   NodePort   10.x.x.x   80:30080/TCP
```

---

## Paso 5 — Verificar el endpoint de salud

Desde WSL2:

```bash
curl http://localhost:30080/api/health/
# {"status": "ok"}
```

Si `localhost` no responde, usar la IP del nodo:

```bash
kubectl get node madrigal -o jsonpath='{.status.addresses[?(@.type=="InternalIP")].address}'
curl http://<IP>:30080/api/health/
```

---

## Paso 6 — Demostrar rolling update sin caída

Abrir dos terminales en WSL2.

**Terminal 1 — health check continuo:**

```bash
while true; do
  curl -s http://localhost:30080/api/health/
  echo " $(date +%T)"
  sleep 0.5
done
```

**Terminal 2 — forzar el rollout:**

```bash
kubectl annotate deployment ihungo-backend -n ihungo \
  rollout-trigger="$(date +%s)" --overwrite

kubectl rollout status deployment/ihungo-backend -n ihungo
```

Durante el rollout, la Terminal 1 debe mantener respuestas `{"status": "ok"}` sin interrupciones. Al terminar el Deployment vuelve a `2/2 Ready`.

---

## Resumen de orden de aplicación

```bash
kubectl apply -f devops/3-k3s/manifests/namespace.yaml
kubectl apply -f devops/3-k3s/manifests/configmap.yaml
# Secret: crear desde CLI (ver Paso 1)
kubectl apply -f devops/3-k3s/manifests/postgres.yaml
kubectl rollout status statefulset/postgres -n ihungo
kubectl apply -f devops/3-k3s/manifests/deployment.yaml
kubectl rollout status deployment/ihungo-backend -n ihungo
kubectl apply -f devops/3-k3s/manifests/service.yaml
curl http://localhost:30080/api/health/
```
