# Backend 4 — API REST de asignación de actividades

API REST construida con Django REST Framework y PostgreSQL.

## Requisitos

- Docker
- Docker Compose

---

## Configuración inicial

```bash
cp .env.example .env
```

Edita `.env` con tus valores reales antes de levantar el proyecto.

---

## Levantar con Docker Compose

```bash
docker compose up --build
```

---

## Ejecutar migraciones

```bash
docker compose exec web python manage.py migrate
```

---

## Probar el healthcheck

```bash
curl http://localhost:8000/api/health/
```

Respuesta esperada:

```json
{"status": "ok"}
```
