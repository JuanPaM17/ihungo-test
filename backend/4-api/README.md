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
docker compose exec web python manage.py test users activities registrations bulk_upload
```

---

## Endpoints disponibles

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/health/` | Healthcheck |
| POST | `/api/auth/token/` | Obtener JWT |
| POST | `/api/auth/token/refresh/` | Refrescar JWT |
| GET | `/api/asociados/` | Listar asociados |
| POST | `/api/asociados/` | Crear asociado |
| GET | `/api/actividades/` | Listar actividades |
| POST | `/api/actividades/` | Crear actividad |
| PATCH | `/api/actividades/{id}/` | Actualizar actividad |
| DELETE | `/api/actividades/{id}/` | Eliminar actividad |
| POST | `/api/carga-masiva/asociados/` | Carga masiva de asociados (CSV/XLSX) |
| POST | `/api/carga-masiva/actividades/` | Carga masiva de actividades (CSV/XLSX) |

### Filtros de actividades

```
GET /api/actividades/?desde=2026-10-01
GET /api/actividades/?hasta=2026-10-31
GET /api/actividades/?desde=2026-10-01&hasta=2026-10-31
```

---

## Django Admin

```
http://localhost:8000/admin/
```

Modelos disponibles: **Users**, **Asociados**, **Activities**, **Registration Requests**

---

## Carga masiva (Fase 7)

Solo administradores pueden usar estos endpoints. Aceptan `multipart/form-data` con un campo `file` (`.csv` o `.xlsx`).

### Formato CSV de asociados

```
identificacion,nombre,apellidos,email,ciudad
123456,Juan,Perez,juan@example.com,Bogota
```

### Formato CSV de actividades

```
tipo_actividad,descripcion,fecha_inicio,fecha_fin,asociado_email
workshop,Taller de Python,2027-01-01T09:00:00Z,2027-01-01T11:00:00Z,assoc@example.com
```

Tipos de actividad válidos: `workshop`, `seminar`, `meeting`, `training`, `other`

### Respuesta

```json
{
  "created": 2,
  "failed": 1,
  "errors": [
    {"row": 3, "code": "DUPLICATE_EMAIL", "detail": "Email duplicado: ..."}
  ]
}
```

### Ejemplo bash

```bash
curl -X POST http://localhost:8000/api/carga-masiva/asociados/ \
  -H "Authorization: Bearer <token>" \
  -F "file=@asociados.csv"
```

```powershell
$token = "..."
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/carga-masiva/asociados/ `
  -Headers @{ Authorization = "Bearer $token" } `
  -Form @{ file = Get-Item asociados.csv }
```

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
