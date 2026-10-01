# DevOps 1 — GitHub Actions → Docker Hub

Automatización del ciclo completo de validación, construcción, análisis de vulnerabilidades
y publicación de la imagen Docker del Backend 4 mediante GitHub Actions.

---

## Archivos relevantes

```
ihungo-test/
├── .github/
│   └── workflows/
│       └── ci-dockerhub.yml        # Pipeline principal
└── backend/
    └── 4-api/
        ├── Dockerfile               # Multi-stage, usuario no-root
        ├── entrypoint.sh            # migrate + collectstatic + gunicorn
        ├── .dockerignore            # Excluye .env, venv, cache, staticfiles
        ├── requirements.txt         # Django 5.1, DRF, gunicorn, ruff, pytest
        └── pyproject.toml           # Configuración de ruff, pytest y coverage
```

El workflow apunta a `context: backend/4-api`, de modo que el Dockerfile y el código
fuente del backend son los únicos artefactos que entran en el contexto de construcción.

---

## Repositorios

| Recurso | URL |
|---|---|
| Repositorio principal (GitLab) | https://gitlab.com/personal-group5360139/ihungo-test |
| Espejo para GitHub Actions | https://github.com/JuanPaM17/ihungo-test |
| Docker Hub — repositorio | https://hub.docker.com/r/juanpablomc/ihungo-backend |
| Docker Hub — etiquetas | https://hub.docker.com/r/juanpablomc/ihungo-backend/tags |

El repositorio de GitLab es el origen del trabajo. El repositorio de GitHub actúa como
espejo y es el que ejecuta GitHub Actions.

---

## Secrets configurados

Configurados en `Settings → Secrets and variables → Actions` del repositorio de GitHub:

| Secret | Uso |
|---|---|
| `DOCKERHUB_USERNAME` | Usuario de Docker Hub (`juanpablomc`) |
| `DOCKERHUB_TOKEN` | Access token de Docker Hub (no contraseña) |

Ningún valor real se encuentra versionado en el repositorio.

---

## Pipeline

Archivo: `.github/workflows/ci-dockerhub.yml`

### Disparadores

| Evento | Comportamiento |
|---|---|
| `push` a `main` | Ejecuta calidad + build + push |
| `push` de tag `v*` | Ejecuta calidad + build + push |
| `pull_request` a `main` | Ejecuta calidad + build + scan (sin push) |

### Diagrama de jobs

```
push / pull_request / tag
          |
          v
   ┌─────────────────┐
   │  quality        │  Job 1
   │  ─────────────  │
   │  ruff check     │
   │  makemigrations │
   │  migrate        │
   │  pytest + cov   │
   └────────┬────────┘
            │ needs: [quality]
            v
   ┌─────────────────────────┐
   │  build-scan-push        │  Job 2
   │  ─────────────────────  │
   │  Docker Buildx setup    │
   │  Login (solo non-PR)    │
   │  Metadata + etiquetas   │
   │  Build local (load)     │
   │  Trivy scan → SARIF     │
   │  Push (solo non-PR)     │
   └─────────────────────────┘
```

### Job 1 — `quality` (Lint & Tests)

Corre sobre `ubuntu-latest` con un servicio PostgreSQL (`postgres:16-alpine`) para que
las pruebas tengan base de datos disponible.

Variables de entorno inyectadas al job:

```
DJANGO_SECRET_KEY    ci-secret-key-not-used-in-production
DJANGO_DEBUG         True
DJANGO_ALLOWED_HOSTS localhost,127.0.0.1
POSTGRES_DB          ci_db
POSTGRES_USER        ci_user
POSTGRES_PASSWORD    ci_password
POSTGRES_HOST        localhost
POSTGRES_PORT        5432
```

Pasos ejecutados desde `working-directory: backend/4-api`:

```bash
pip install -r requirements.txt

ruff check .
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
pytest --cov=. --cov-report=term-missing --cov-report=xml --cov-fail-under=80
```

El artefacto `coverage.xml` se sube y retiene 7 días.

### Job 2 — `build-scan-push` (Build · Scan · Push)

Depende de `quality`. Si el job anterior falla, este no se ejecuta.

**Etiquetas generadas** (con `docker/metadata-action@v5`, `latest=false`):

| Evento | Etiquetas producidas |
|---|---|
| Push a `main` | `main`, `sha-<commit-corto>` |
| Tag `v1.2.3` | `1.2.3`, `1.2`, `sha-<commit-corto>` |
| Pull request | `sha-<commit-corto>` (sin push) |

**Flujo de build:**

1. Se construye la imagen con `push: false, load: true` (carga en el daemon local).
2. Trivy escanea la imagen local buscando vulnerabilidades `CRITICAL` y `HIGH`.
3. El resultado SARIF se sube a la pestaña Security del repositorio.
4. Si el evento no es un PR, se ejecuta un segundo build con `push: true` hacia Docker Hub.
   Se reutiliza la caché GHA (`cache-from/cache-to: type=gha`) para acelerar el paso.

---

## Dockerfile

El Dockerfile de referencia del reto fue reemplazado por una versión multi-stage con
mejoras de seguridad y optimización de tamaño.

### Stage 1 — builder

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
```

Instala las dependencias en `/install` sin cache de pip. Este stage no llega a la imagen final.

### Stage 2 — runtime

```dockerfile
FROM python:3.12-slim AS runtime
# Copia solo los paquetes instalados, no pip ni el cache
COPY --from=builder /install /install
# Usuario sin privilegios
RUN groupadd --system appgroup && useradd --system --gid appgroup --no-create-home appuser
COPY . .
RUN chmod +x entrypoint.sh && mkdir -p staticfiles && chown -R appuser:appgroup /app
USER appuser
EXPOSE 8000
CMD ["./entrypoint.sh"]
```

### entrypoint.sh

```sh
#!/bin/sh
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn config.wsgi:application -c gunicorn.conf.py
```

Las migraciones y la colección de estáticos se ejecutan en el arranque del contenedor,
antes de levantar gunicorn.

### .dockerignore

Excluye del contexto de build:

```
.env / .env.*       # Secretos locales
.venv / venv        # Entorno virtual
__pycache__         # Bytecode Python
.pytest_cache       # Caché de pruebas
.ruff_cache         # Caché del linter
staticfiles/        # Generados en runtime por collectstatic
docker-compose*     # Solo para desarrollo local
.git/               # Historia de Git
```

Esto reduce el contexto de build y evita incorporar secretos o archivos innecesarios
en la imagen.

---

## Defectos corregidos respecto al workflow de referencia

### FIX-1 — Push sin validación previa

**Problema:** el workflow de referencia construía y publicaba la imagen sin ejecutar lint
ni pruebas.

**Riesgo:** una imagen con errores de código o regresiones podía publicarse en Docker Hub.

**Corrección:** se creó el job `quality` como prerequisito obligatorio de `build-scan-push`
mediante `needs: [quality]`. El build no puede iniciarse si lint o pruebas fallan.

---

### FIX-2 — Push durante Pull Requests

**Problema:** la referencia usa `push: true` sin diferenciar entre push y pull_request.

**Riesgo:** un PR podría publicar una imagen aunque su propósito sea únicamente validar cambios.

**Corrección:** el login y el push final se condicionan a `github.event_name != 'pull_request'`.
Los PRs ejecutan lint, pruebas, build y scan, pero no publican nada.

---

### FIX-3 — Ausencia de escaneo de vulnerabilidades

**Problema:** el workflow de referencia no analizaba vulnerabilidades de la imagen.

**Riesgo:** la imagen podía publicarse con vulnerabilidades conocidas sin evidencia de análisis.

**Corrección:** se incorporó `aquasecurity/trivy-action` al pipeline. La imagen se construye
localmente primero (`load: true`) y Trivy la escanea antes de decidir si publicar.
El resultado se sube en formato SARIF a la pestaña Security del repositorio de GitHub.

---

### FIX-4 — Etiquetado sin trazabilidad

**Problema:** la referencia generaba la etiqueta `latest` implícitamente.

**Riesgo:** es imposible saber qué commit originó una imagen etiquetada como `latest`.

**Corrección:** `latest=false` en la configuración de metadata. Solo se generan etiquetas
trazables: `main`, `sha-<commit>` y semver `vX.Y.Z` / `X.Y` cuando se publica un tag.

---

### FIX-5 — Login en Pull Requests de forks

**Problema:** el step de login ocurría también en PR, exponiendo el token de Docker Hub
a código de forks potencialmente maliciosos.

**Riesgo:** un fork podría exfiltrar el `DOCKERHUB_TOKEN` mediante el contexto del runner.

**Corrección:** el step de login incluye `if: github.event_name != 'pull_request'`,
de modo que el token nunca se usa en ejecuciones de PR.

---

## Evidencias

Las capturas se encuentran en `devops/screenshots/`.

| # | Captura | Qué demuestra |
|---|---|---|
| 01 | `01-pipeline-main.png` | Pipeline completo ejecutado exitosamente desde `main` |
| 02 | `02-lint-tests.png` | `ruff`, migraciones, `pytest` y cobertura >= 80% pasando |
| 03 | `03-build-scan-push.png` | Build Docker, escaneo Trivy y push a Docker Hub |
| 04 | `04-dockerhub-tags.png` | Etiquetas `main` y `sha-<commit>` visibles en Docker Hub |

Ejecucion de referencia en GitHub Actions:
https://github.com/JuanPaM17/ihungo-test/actions/runs/36473605121
