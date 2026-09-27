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

---

## CI/CD

El pipeline de GitLab CI se define en `.gitlab-ci.yml` en la raíz del repositorio y se ejecuta en cada push a cualquier rama.

### Etapas

| Etapa | Job | Qué valida |
|---|---|---|
| `lint` | `lint` | `ruff check .` — estilo e imports |
| `test` | `test` | Migraciones, pytest, cobertura ≥ 80% |
| `build` | `build` | `docker build` de la imagen del backend |

### lint

Ejecuta `ruff check .` con la configuración de `pyproject.toml`. Falla si hay errores de estilo, imports no usados o imports desordenados.

Para reproducir localmente:

```bash
docker compose exec web ruff check .
```

### Migraciones

Antes de los tests el pipeline verifica que no haya migraciones sin versionar:

```bash
python manage.py makemigrations --check --dry-run
```

Si alguien modifica un modelo sin generar la migración, este paso falla.

### Tests y cobertura

Ejecuta `pytest` con cobertura mínima del 80%. La cobertura actual es ~91%.

Para reproducir localmente:

```bash
docker compose exec web pytest --cov=. --cov-report=term-missing --cov-fail-under=80
```

Falla si: algún test falla, o la cobertura total cae por debajo del 80%.

### Docker build

Valida que la imagen puede construirse correctamente:

```bash
docker build -t ihungo-backend:ci .
```

No publica imágenes en ningún registry.

### Variables de CI

Todas las variables usadas en el pipeline son exclusivas de CI y no contienen secretos reales. Si en el futuro se necesita publicar imágenes, agregar estas variables en **GitLab → Settings → CI/CD → Variables**:

- `CI_REGISTRY_USER`
- `CI_REGISTRY_PASSWORD`
- `CI_REGISTRY_IMAGE`
