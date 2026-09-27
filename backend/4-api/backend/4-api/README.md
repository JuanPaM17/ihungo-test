# Backend 4 — API REST de asignación de actividades

API REST construida con Django REST Framework y PostgreSQL, servida con Gunicorn detrás de Nginx.

## Requisitos

- Docker
- Docker Compose

---

## Configuración inicial

```bash
cp .env.example .env
```

Edita `.env` con tus valores reales antes de levantar el proyecto.

> Para desarrollo local puedes poner `DJANGO_DEBUG=True` y `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1`.

---

## Levantar con Docker Compose

```bash
docker compose up --build
```

Esto reconstruye la imagen, ejecuta migraciones, recolecta archivos estáticos e inicia Gunicorn y Nginx automáticamente.

---

## Crear superusuario

```bash
docker compose exec web python manage.py createsuperuser
```

---

## Correr tests

```bash
docker compose exec web python manage.py test common users activities registrations bulk_upload
```

---

## Endpoints disponibles

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/health/` | Healthcheck |
| GET | `/api/schema/` | Schema OpenAPI (YAML) |
| GET | `/api/docs/` | Swagger UI |
| POST | `/api/auth/token/` | Obtener JWT |
| POST | `/api/auth/token/refresh/` | Refrescar JWT |
| POST | `/api/registro/` | Solicitud pública de registro |
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

## Arquitectura

```
Cliente (puerto 80)
       │
       ▼
  Nginx :80
       │
       ├─ /static/  ──→  archivos estáticos (sin pasar por Django)
       │
       └─ /api/, /admin/, /api/docs/, /api/schema/
               │
               ▼
       Gunicorn :8000
               │
               ▼
       Django REST Framework
               │
               ▼
       PostgreSQL :5432
```

---

## URLs de prueba

```
http://localhost/api/health/
http://localhost/api/docs/
http://localhost/api/schema/
http://localhost/admin/
```

---

## Django Admin

```
http://localhost/admin/
```

Modelos disponibles: **Users**, **Asociados**, **Activities**, **Registration Requests**

---

## Carga masiva

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

### Ejemplo

```bash
curl -X POST http://localhost/api/carga-masiva/asociados/ \
  -H "Authorization: Bearer <token>" \
  -F "file=@asociados.csv"
```

```powershell
$token = "..."
Invoke-RestMethod -Method Post -Uri http://localhost/api/carga-masiva/asociados/ `
  -Headers @{ Authorization = "Bearer $token" } `
  -Form @{ file = Get-Item asociados.csv }
```

---

## Autenticación JWT

### Obtener token

```bash
curl -X POST http://localhost/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"tu_password"}'
```

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost/api/auth/token/ `
  -ContentType "application/json" `
  -Body '{"email":"user@example.com","password":"tu_password"}'
```

### Endpoint autenticado vía Nginx

```bash
TOKEN="..."
curl http://localhost/api/asociados/ -H "Authorization: Bearer $TOKEN"
```

```powershell
$token = "..."
Invoke-RestMethod -Uri http://localhost/api/asociados/ `
  -Headers @{ Authorization = "Bearer $token" }
```

---

## Verificar Gunicorn

```bash
docker compose logs web
```

Deberías ver líneas como:

```
[INFO] Starting gunicorn
[INFO] Listening at: http://0.0.0.0:8000
[INFO] Worker booted (pid: ...)
```

## Verificar Nginx

```bash
docker compose logs nginx
```
