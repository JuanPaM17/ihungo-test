# ihungo — Prueba Técnica

Repositorio completo de la prueba técnica ihungo. Contiene cinco retos de backend, dos de IA y tres de DevOps.

---

## Estructura del repositorio

```
ihungo-test/
├── backend/
│   ├── 1-analisis/       # Análisis de arquitectura de una app Django existente
│   ├── 2-refactor/       # Refactorización de código de análisis de sentimientos
│   ├── 3-bouncy/         # Algoritmo Bouncy Numbers en Python y TypeScript
│   └── 4-api/            # API REST de asociados y actividades (Django + PostgreSQL)
├── ia/
│   ├── 1-agente/         # Agente conversacional LLM (LangGraph + FastAPI)
│   └── 2-co-creacion/    # Co-creación guiada: carga masiva de asociados
├── devops/
│   ├── 1-github-actions/ # Pipeline CI/CD con GitHub Actions → Docker Hub
│   ├── 2-jenkins/        # Pipeline CI/CD con Jenkins
│   └── 3-k3s/            # Despliegue del backend en clúster k3s local
├── bruno/                # Colecciones Bruno para todos los endpoints de Backend 4
├── AI_USAGE.md           # Declaración de uso de IA durante la prueba
└── README.md
```

---

## Backend

### Backend 1 — Análisis de arquitectura

Análisis estático de una aplicación Django REST Framework existente. Se identificaron capas, responsabilidades, malas prácticas y oportunidades de mejora.

- Documentos: `backend/1-analisis/ANALISIS.md`, `backend/1-analisis/MALAS_PRACTICAS.md`

### Backend 2 — Refactorización

Refactorización de un script de análisis de sentimientos. Se separaron responsabilidades, se eliminó código duplicado y se mejoró la legibilidad sin cambiar el comportamiento externo.

- Código: `backend/2-refactor/sentiment_analysis_refactor/`

### Backend 3 — Bouncy Numbers

Implementación del algoritmo para encontrar el menor número en el que la proporción de *bouncy numbers* alcanza exactamente un porcentaje dado. Implementado en Python y TypeScript con tests y CLI.

| Porcentaje | Resultado |
|---|---|
| 50 % | 538 |
| 90 % | 21 780 |
| 99 % | 1 587 000 |

- Código: `backend/3-bouncy/python/` y `backend/3-bouncy/typescript/`

**Ejecutar (Python):**
```bash
cd backend/3-bouncy/python
python bouncy.py 99
pytest test_bouncy.py -v
```

**Ejecutar (TypeScript):**
```bash
cd backend/3-bouncy/typescript
npm install
npm run cli 99
npm test
```

### Backend 4 — API REST de asociados y actividades

API REST completa para gestión de asociados y actividades, con autenticación JWT, control de permisos por rol, validación de solapamientos de horario, carga masiva de asociados y documentación OpenAPI.

| Componente | Tecnología |
|---|---|
| Framework | Django 5.1 + Django REST Framework 3.15 |
| Autenticación | SimpleJWT (Bearer token) — rol incluido en el JWT |
| Base de datos | PostgreSQL 16 |
| Servidor | Gunicorn + WhiteNoise |
| Documentación | drf-spectacular (OpenAPI 3) |
| Tests | pytest + pytest-django + pytest-cov |
| Linting | ruff |

**Levantar con Docker Compose:**
```bash
cd backend/4-api
cp .env.example .env   # ajustar variables
docker compose up --build
```

Endpoints principales:
- `POST /api/auth/token/` — obtener JWT
- `GET/POST /api/asociados/` — listar y crear asociados
- `GET/POST /api/actividades/` — listar y crear actividades
- `GET /api/actividades/disponibilidad/` — consultar disponibilidad de asociados
- `POST /api/asociados/bulk-upload/` — carga masiva desde XLSX/CSV
- `GET /api/docs/` — documentación OpenAPI interactiva

- README completo: `backend/4-api/README.md`

---

## IA

### IA 1 — Agente conversacional

Agente conversacional para gestión de actividades y asociados, construido con LangGraph y expuesto vía FastAPI. Soporta dos roles: administrador (acceso total) y asociado (solo sus propias actividades).

**Arquitectura V2:**

```
FastAPI (server.py)
    └── Supervisor (LangGraph)
            ├── greeting_agent
            ├── actividades_agent      (list, create, update, delete, disponibilidad)
            └── asociados_agent        (list, buscar, obtener, crear, actualizar, eliminar)
                    └── Evaluator → Summarizer
```

- Proveedor LLM configurable: OpenAI o Gemini vía variable de entorno
- Autenticación JWT — rol extraído del token para routing dinámico
- Sesión conversacional independiente del JWT (`X-Session-Id`)
- Herramientas con protocolo de confirmación antes de operaciones de escritura
- Streaming SSE disponible en `/llm/v2/ihungo/stream`
- Observabilidad estructurada por turno en `logs/agent.jsonl`
- CLI conversacional incluido (`cli.py`)
- Tests automatizados con proveedores simulados
- Evaluaciones del agente: `ia/1-agente/evals/`

**Levantar:**
```bash
cd ia/1-agente
cp .env.example .env   # ajustar OPENAI_API_KEY y API_ENDPOINT
pip install -r requirements.txt
uvicorn server:app --port 8001
```

**CLI:**
```bash
python cli.py
```

**Tests:**
```bash
pytest tests/ -v
```

- README completo: `ia/1-agente/README.md`
- Evidencias: `ia/1-agente/EVIDENCIAS.md`

### IA 2 — Co-creación guiada

Ejercicio de co-creación con asistente de IA para diseñar e implementar la funcionalidad de carga masiva de asociados del Backend 4. Incluye historias de usuario, diseño, plan de trabajo, reglas entregadas al asistente y bitácora de decisiones.

- Documentos: `ia/2-co-creacion/specs/`
- Respuestas al cuestionario: `ia/2-co-creacion/RESPUESTAS.md`

---

## DevOps

### DevOps 1 — GitHub Actions

Pipeline CI/CD para el Backend 4 que ejecuta lint, tests, build de imagen Docker, escaneo de vulnerabilidades con Trivy y push a Docker Hub. El push solo ocurre en `main` o tags `v*`, nunca en pull requests.

| Recurso | URL |
|---|---|
| Espejo GitHub (Actions) | https://github.com/JuanPaM17/ihungo-test |
| Docker Hub — repositorio | https://hub.docker.com/r/juanpablomc/ihungo-backend |
| Docker Hub — etiquetas | https://hub.docker.com/r/juanpablomc/ihungo-backend/tags |

- Workflow: `.github/workflows/ci-dockerhub.yml`
- README completo: `devops/1-github-actions/README.md`

Etapas:
1. Lint (ruff)
2. Tests + cobertura (pytest)
3. Docker build
4. Escaneo Trivy
5. Push a Docker Hub con etiquetas trazables (`main`, `sha-<commit>`, `vX.Y.Z`)

### DevOps 2 — Jenkins

Pipeline equivalente al de GitHub Actions implementado en Jenkins.

- Archivos: `devops/2-jenkins/`

### DevOps 3 — Despliegue en k3s

Despliegue del Backend 4 en un clúster k3s local sobre WSL2 con 2 réplicas, PostgreSQL como StatefulSet, ConfigMap, Secret y Service NodePort. Incluye rolling update sin downtime.

```
devops/3-k3s/manifests/
├── namespace.yaml
├── configmap.yaml
├── secret.yaml
├── postgres.yaml     # StatefulSet PostgreSQL
├── deployment.yaml   # 2 réplicas del backend
└── service.yaml      # NodePort :30080
```

**Aplicar manifiestos:**
```bash
kubectl apply -f devops/3-k3s/manifests/
```

- README completo: `devops/3-k3s/README.md`
- Evidencias: `devops/EVIDENCIAS.md`

---

## Colecciones Bruno

Colecciones organizadas para probar todos los endpoints del Backend 4:

```
bruno/
├── auth/
├── asociados/
├── actividades/
├── carga-masiva/
├── health/
└── environments/
```

---

## Uso de IA

Ver `AI_USAGE.md` para la declaración completa de herramientas y decisiones tomadas durante la prueba.
