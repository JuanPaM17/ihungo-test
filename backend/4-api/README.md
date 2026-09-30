# Backend 4 — API REST de asignación de actividades

API REST para gestión de asociados y actividades, construida con Django REST Framework, PostgreSQL, Gunicorn y Nginx.

---

## Tecnologías

| Componente | Tecnología |
|---|---|
| Framework | Django 5.1 + Django REST Framework 3.15 |
| Autenticación | SimpleJWT (Bearer token) |
| Base de datos | PostgreSQL 16 |
| Servidor de aplicación | Gunicorn 22 |
| Reverse proxy | Nginx 1.27 |
| Contenedores | Docker + Docker Compose |
| Documentación API | drf-spectacular (OpenAPI 3) |
| Carga masiva | openpyxl (XLSX) + csv (stdlib) |
| Tests | pytest + pytest-django + pytest-cov |
| Linting | ruff |

---

## Arquitectura

```
Cliente (puerto 80)
        |
        v
   Nginx :80
        |
        +-- /static/  -->  archivos estáticos (volumen compartido)
        |
        +-- /api/, /admin/, /api/docs/
                |
                v
        Gunicorn :8000
                |
                v
        Django REST Framework
                |
                +-- Views / ViewSets   (HTTP, autenticación, permisos)
                +-- Serializers        (validación de estructura)
                +-- Services           (reglas de negocio)
                +-- Models / ORM
                        |
                        v
                PostgreSQL :5432
```

---

## Requisitos

- Docker
- Docker Compose

---

## Variables de entorno

Copiar `.env.example` y ajustar los valores:

```bash
cp .env.example .env
```

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DJANGO_SECRET_KEY` | Clave secreta de Django | cadena aleatoria larga |
| `DJANGO_DEBUG` | Modo debug | `True` (dev) / `False` (prod) |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos separados por coma | `localhost,127.0.0.1` |
| `POSTGRES_DB` | Nombre de la base de datos | `api_db` |
| `POSTGRES_USER` | Usuario de PostgreSQL | `api_user` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | `api_password` |
| `POSTGRES_HOST` | Host de PostgreSQL | `db` |
| `POSTGRES_PORT` | Puerto de PostgreSQL | `5432` |

> `.env` nunca debe versionarse. `.env.example` contiene únicamente valores de ejemplo.

---

## Ejecución con Docker

```bash
docker compose up --build
```

Este comando reconstruye la imagen (multi-stage), ejecuta migraciones, recolecta archivos estáticos e inicia Gunicorn y Nginx.

### Verificar que el proceso no corre como root

```bash
# Ver el usuario del proceso principal dentro del contenedor
docker compose exec web whoami
# Esperado: appuser

# Ver el UID/GID del proceso gunicorn
docker compose exec web id
# Esperado: uid=999(appuser) gid=999(appgroup)

# Confirmar directamente con ps
docker compose exec web ps aux
# La columna USER debe mostrar appuser, no root
```

### Build standalone (sin Compose)

```bash
# Construir la imagen
docker build -t ihungo-backend:local .

# Verificar que no hay capas con secretos (secrets solo en .env, nunca en la imagen)
docker history ihungo-backend:local

# Inspecionar usuario efectivo
docker run --rm --entrypoint whoami ihungo-backend:local
# Esperado: appuser
```

---

## Migraciones

Las migraciones ya están versionadas. Para generarlas tras cambiar un modelo:

```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

Para verificar que no haya migraciones pendientes sin versionar:

```bash
docker compose exec web python manage.py makemigrations --check --dry-run
```

---

## Crear superusuario

```bash
docker compose exec web python manage.py createsuperuser
```

---

## Endpoints

| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| GET | `/api/health/` | No | Healthcheck |
| GET | `/api/schema/` | No | Schema OpenAPI (YAML) |
| GET | `/api/docs/` | No | Swagger UI |
| POST | `/api/auth/token/` | No | Obtener JWT |
| POST | `/api/auth/token/refresh/` | No | Refrescar JWT |
| POST | `/api/registro/` | No | Solicitud pública de registro |
| GET | `/api/asociados/` | JWT | Listar asociados (con filtros opcionales) |
| POST | `/api/asociados/` | JWT Admin | Crear asociado |
| GET | `/api/asociados/{id}/` | JWT | Obtener detalle de un asociado |
| PATCH | `/api/asociados/{id}/` | JWT Admin | Actualizar parcialmente un asociado |
| DELETE | `/api/asociados/{id}/` | JWT Admin | Eliminar asociado |
| GET | `/api/actividades/` | JWT | Listar actividades |
| POST | `/api/actividades/` | JWT Admin | Crear actividad |
| PATCH | `/api/actividades/{id}/` | JWT | Actualizar actividad |
| DELETE | `/api/actividades/{id}/` | JWT | Eliminar actividad |
| POST | `/api/carga-masiva/asociados/` | JWT Admin | Carga masiva de asociados (CSV/XLSX) |
| POST | `/api/carga-masiva/actividades/` | JWT Admin | Carga masiva de actividades (CSV/XLSX) |

### Filtros de actividades

```
GET /api/actividades/?desde=2026-10-01
GET /api/actividades/?hasta=2026-10-31
GET /api/actividades/?desde=2026-10-01&hasta=2026-10-31
```

---

## Autenticación JWT

### Obtener token

```bash
curl -X POST http://localhost/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"tu_password"}'
```

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost/api/auth/token/ `
  -ContentType "application/json" `
  -Body '{"email":"admin@example.com","password":"tu_password"}'
```

Respuesta:

```json
{
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}
```

### Usar token

```bash
curl http://localhost/api/asociados/ \
  -H "Authorization: Bearer <access_token>"
```

```powershell
Invoke-RestMethod -Uri http://localhost/api/asociados/ `
  -Headers @{ Authorization = "Bearer <access_token>" }
```

---

## Ejemplos de uso

### Crear actividad

```bash
curl -X POST http://localhost/api/actividades/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "activity_type": "workshop",
    "description": "Taller de Python",
    "start_datetime": "2027-01-01T09:00:00Z",
    "end_datetime": "2027-01-01T11:00:00Z",
    "asociado": 1
  }'
```

### Crear asociado (admin)

```bash
curl -X POST http://localhost/api/asociados/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nuevo@example.com",
    "password": "segura1234",
    "identification": "123456789",
    "first_name": "Nuevo",
    "last_name": "Asociado",
    "city": "Bogotá"
  }'
```

### Actualizar asociado (admin)

```bash
curl -X PATCH http://localhost/api/asociados/1/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"city": "Medellín"}'
```

### Eliminar asociado (admin)

```bash
curl -X DELETE http://localhost/api/asociados/1/ \
  -H "Authorization: Bearer <token>"
```

> Si el asociado tiene actividades asociadas, devuelve `409` con `{"code": "HAS_ACTIVITIES", "detail": "..."}`. Elimina primero las actividades.

### Solicitud pública de registro

```bash
curl -X POST http://localhost/api/registro/ \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Juan","last_name":"Perez","email":"juan@example.com"}'
```

---

## Carga masiva

Solo administradores. `multipart/form-data` con campo `file` (`.csv` o `.xlsx`).

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

Tipos válidos: `workshop`, `seminar`, `meeting`, `training`, `other`

### Respuesta

```json
{
  "created": 2,
  "failed": 1,
  "errors": [
    {"row": 3, "code": "DUPLICATE_EMAIL", "detail": "..."}
  ]
}
```

Códigos de error por fila: `INVALID_EMAIL`, `DUPLICATE_EMAIL`, `DUPLICATE_IDENTIFICATION`, `INVALID_DATA`, `ASOCIADO_NOT_FOUND`, `INVALID_DATE`, `INVALID_DATE_RANGE`, `ACTIVITY_OVERLAP`.

```bash
curl -X POST http://localhost/api/carga-masiva/asociados/ \
  -H "Authorization: Bearer <token>" \
  -F "file=@asociados.csv"
```

---

## Reglas de negocio

- `fecha_fin` debe ser estrictamente posterior a `fecha_inicio` (400 si no se cumple).
- No pueden existir dos actividades con fechas solapadas para el mismo asociado (409).
- Las actividades pasadas son de solo lectura para asociados (403).
- La carga masiva procesa cada fila independientemente: las filas válidas se crean aunque otras fallen.
- No se puede eliminar un asociado que tenga actividades asociadas (409 `HAS_ACTIVITIES`). Se deben eliminar primero sus actividades.
- Una solicitud de registro inicia siempre en estado `pendiente`.
- No se puede aprobar o rechazar una solicitud que no esté pendiente.
- Al aprobar una solicitud se crea automáticamente el usuario y el perfil de asociado.

---

## Permisos

| Acción | Admin | Asociado propio | Asociado otro | Anónimo |
|---|---|---|---|---|
| Listar actividades | Todas | Las propias | — | 401 |
| Crear actividad | Sí | 403 | 403 | 401 |
| Modificar actividad futura | Sí | Sí | 403 | 401 |
| Modificar actividad pasada | Sí | 403 | 403 | 401 |
| Eliminar actividad | Sí | Solo futuras propias | 403 | 401 |
| Listar asociados | Sí | Sí | Sí | 401 |
| Ver detalle asociado | Sí | Sí | Sí | 401 |
| Crear asociado | Sí | 403 | 403 | 401 |
| Modificar asociado | Sí | 403 | 403 | 401 |
| Eliminar asociado (sin actividades) | Sí | 403 | 403 | 401 |
| Eliminar asociado (con actividades) | 409 | 403 | 403 | 401 |
| Carga masiva | Sí | 403 | 403 | 401 |
| Solicitud de registro | — | — | — | Público |

---

## OpenAPI / Swagger

```
http://localhost/api/docs/      <- Swagger UI interactivo
http://localhost/api/schema/    <- Schema YAML descargable
```

El schema incluye autenticación JWT, todos los endpoints, request/response y códigos HTTP relevantes.

---

## Panel administrativo

```
http://localhost/admin/
```

Desde el admin:
- Aprobar o rechazar solicitudes de registro en lote.
- Gestionar usuarios, asociados y actividades.

---

## Principios SOLID

### S — Single Responsibility Principle

Cada módulo tiene una única razón para cambiar:

- `activities/services.py`: lógica de negocio pura (`validate_date_range`, `validate_no_overlap`, `create_activity`, `update_activity`). No sabe nada de HTTP.
- `activities/permissions.py`: decide si el usuario puede acceder al objeto. No valida datos ni ejecuta lógica de negocio.
- `bulk_upload/parsers.py`: parsea archivos CSV/XLSX a listas de dicts. No valida contenido ni accede a la base de datos.
- `bulk_upload/services.py`: aplica validaciones fila por fila y persiste registros. No sabe de HTTP ni de formatos de archivo.

### O — Open/Closed Principle

Aplicación parcial y honesta:

- `bulk_upload/parsers.py` está abierto a extensión: agregar soporte a un nuevo formato (ej. ODS) requiere añadir `parse_ods` y extender `parse_file` sin modificar el código existente.
- Los serializers usan clases separadas para lectura (`ActivityReadSerializer`) y escritura (`ActivityWriteSerializer`), sin que un cambio en una afecte a la otra.

No se diseñaron jerarquías de herencia para servicios. En un proyecto mayor, un strategy pattern para los parsers aplicaría OCP de forma más estricta.

### L — Liskov Substitution Principle

- `IsAdmin` en `bulk_upload/views.py` extiende `IsAuthenticated` respetando su contrato: unauthenticated devuelve 401, authenticated sin rol devuelve 403. No rompe el comportamiento esperado de la clase base.
- `ActivityPermission` extiende `BasePermission` implementando `has_permission` y `has_object_permission` respetando la interfaz de DRF.

### I — Interface Segregation Principle

- Las vistas de carga masiva declaran explícitamente `parser_classes = [MultiPartParser]` en lugar de heredar el parser global. Cada vista expone solo los parsers que necesita.
- `AsociadoViewSet` declara explícitamente los mixins que necesita (`List`, `Create`, `Retrieve`, `Update`, `Destroy`). Los permisos de escritura (`IsAdmin`) se separan de los de lectura (`IsAuthenticated`) en `get_permissions()`, sin que un cambio en unos afecte a los otros.
- `ActivityViewSet` excluye `RetrieveModelMixin` porque el enunciado no requiere `GET /actividades/{id}/`.

### D — Dependency Inversion Principle

Aplicación parcial y honesta:

- `activities/views.py` depende de `ActivityValidationError` (abstracción) en lugar de capturar errores de ORM directamente. La vista reacciona al código de error sin saber cómo se valida.
- `bulk_upload/services.py` reutiliza `validate_date_range` y `validate_no_overlap` de `activities/services.py`. Depende de las funciones del dominio, no del ORM directamente para las validaciones de negocio.

No existe capa de repositorio ni interfaces formales (Protocol/ABC). En un proyecto con múltiples backends de datos esa sería la extensión natural.

---

## Pruebas

```bash
docker compose exec web pytest
```

| Métrica | Valor |
|---|---|
| Total de tests | ~98 |
| Tests pasando | ~98 |
| Cobertura total | ≥91% |
| Umbral mínimo | 80% |

Los tests cubren: autenticación, permisos, creación/modificación/eliminación de actividades, validación de fechas, solapamientos, CRUD completo de asociados (retrieve/create/update/delete con permisos admin y caso 409 por actividades protegidas), solicitudes de registro, carga masiva CSV/XLSX, endpoints OpenAPI y healthcheck.

### TDD visible en el historial

Las reglas de negocio y permisos fueron desarrolladas con TDD estricto. El historial de git lo evidencia en dos commits consecutivos:

- `40fdff9` — tests escritos primero: fechas, solapamientos y permisos, sin implementación.
- `436229b` — implementacion de `services.py`, `permissions.py` y `views.py` para pasar los tests anteriores.

Esto cubre las reglas mas criticas: validacion de fechas, deteccion de solapamientos y control de acceso por rol y estado de la actividad.

Archivos con menor cobertura:

| Archivo | Cobertura | Nota |
|---|---|---|
| `registrations/admin.py` | 54% | Acciones del Django Admin — difíciles de testear con APIClient |
| `activities/permissions.py` | 86% | Casos extremos del permiso de objeto |
| `bulk_upload/parsers.py` | 88% | Ramas de error en parsing |

---

## Cobertura

```bash
docker compose exec web pytest --cov=. --cov-report=term-missing --cov-fail-under=80
```

---

## Lint

```bash
docker compose exec web ruff check .
```

Configuración en `pyproject.toml`. Reglas activas: `E`, `F`, `W`, `I`. Línea máxima: 120 caracteres.

---

## CI/CD

Pipeline definido en `.gitlab-ci.yml` en la raíz del repositorio. Se ejecuta en cada push a cualquier rama.

| Etapa | Qué valida |
|---|---|
| `lint` | `ruff check .` |
| `test` | Migraciones + pytest + cobertura >= 80% |
| `build` | `docker build` — valida que la imagen compila |

---

## Nginx y Gunicorn

**Gunicorn** corre en el contenedor `web` en el puerto 8000. Configuración en `gunicorn.conf.py` (2 workers, timeout 60s).

**Nginx** actúa como reverse proxy en el puerto 80. Sirve `/static/` directamente desde el volumen compartido sin pasar por Django. El resto del tráfico lo reenvía a Gunicorn.

```bash
docker compose logs web    # logs de Gunicorn
docker compose logs nginx  # logs de Nginx
```

---

## Decisiones técnicas

| Decisión | Alternativa descartada | Razón |
|---|---|---|
| Email como `USERNAME_FIELD` | Username por defecto | El enunciado requiere autenticación por email |
| `Asociado` como modelo separado de `User` | Campos extra en `User` | Permite tener admins sin datos de asociado |
| Servicios como funciones puras | Métodos en el modelo | Más simples de testear, sin estado |
| Detección XLSX por magic bytes | Solo por extensión | DRF no siempre propaga el nombre del archivo en tests |
| `ruff` en lugar de flake8+isort+black | Múltiples herramientas | Una sola herramienta cubre lint, imports y formato |
| Gunicorn en `entrypoint.sh` | CMD directo en Dockerfile | Permite ejecutar `migrate` y `collectstatic` antes de arrancar |
| Overlap: `start < new_end AND end > new_start` | Comparación simple | Detecta todos los casos de solapamiento parcial |
