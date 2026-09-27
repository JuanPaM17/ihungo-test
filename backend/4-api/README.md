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

## Migraciones

```bash
docker compose exec web python manage.py makemigrations users activities registrations
docker compose exec web python manage.py migrate
```

---

## Crear superusuario

```bash
docker compose exec web python manage.py createsuperuser
```

---

## Correr tests

```bash
docker compose exec web python manage.py test users activities registrations
```

---

## Django Admin

```
http://localhost:8000/admin/
```

Modelos disponibles: **Users**, **Asociados**, **Activities**, **Registration Requests**

---

## Probar el healthcheck

```bash
curl http://localhost:8000/api/health/
```

```powershell
Invoke-RestMethod -Uri http://localhost:8000/api/health/
```

Respuesta esperada:

```json
{"status": "ok"}
```

---

## Autenticación JWT

### Obtener token

```bash
curl -X POST http://localhost:8000/api/auth/token/ -H "Content-Type: application/json" -d '{"email":"user@example.com","password":"tu_password"}'
```

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/auth/token/ -ContentType "application/json" -Body '{"email":"user@example.com","password":"tu_password"}'
```

### Refrescar token

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ -H "Content-Type: application/json" -d '{"refresh":"el_refresh_token_aqui"}'
```

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/auth/token/refresh/ -ContentType "application/json" -Body '{"refresh":"el_refresh_token_aqui"}'
```
