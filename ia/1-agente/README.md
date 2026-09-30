# Agente IA — ihungo

Agente conversacional para la gestión de actividades y asociados de ihungo, construido con LangGraph + FastAPI.

## Índice

1. [Estructura del Proyecto](#1-estructura-del-proyecto)
2. [Flujo Principal (`server.py`)](#2-flujo-principal-serverpy)
3. [Asistente V1](#3-asistente-v1)
4. [Asistente V2](#4-asistente-v2)
5. [Variables de Entorno](#5-variables-de-entorno)
6. [Configuración Dinámica — tenant ihungo](#6-configuración-dinámica--tenant-ihungo)
7. [Instalación y Arranque](#7-instalación-y-arranque)
8. [Tests Automatizados](#8-tests-automatizados)
9. [Evaluaciones del Agente](#9-evaluaciones-del-agente)
10. [CLI Conversacional](#10-cli-conversacional)

---

## 1. Estructura del Proyecto

```
ia/1-agente/
├── config/
│   ├── v1/
│   │   └── tools_config.json               # Herramientas para V1
│   └── v2/
│       ├── prompts/
│       │   ├── general_prompt.md           # Instrucciones globales del sistema
│       │   ├── evaluator_prompt.md         # Prompt del evaluador de respuestas
│       │   └── summarizer_prompt.md        # Prompt del nodo resumen
│       └── tenants/
│           └── ihungo/
│               ├── dynamic_agents_config.json   # Agentes y supervisor de ihungo
│               └── prompts/
│                   ├── supervisor_prompt.md
│                   └── agents/
│                       ├── greeting_agent.md
│                       └── actividades_agent.md
├── tools/
│   ├── actividades/
│   │   └── actividades_tool.py     # list, create, update, delete actividades
│   ├── asociados/
│   │   └── asociados_tool.py       # list asociados
│   ├── system/
│   │   └── system.py               # get_datetime, invalidate_cache
│   └── utils/
│       └── datetime_tool.py        # GetCurrentDatetimeTool (V1)
├── utils/
│   ├── agents.py                   # Registro global de tools y carga de agentes
│   ├── request.py                  # ApiRequestManager (Authorization: Bearer)
│   ├── date_time.py                # get_current_timestamp (America/Bogota)
│   └── tenant_config.py            # Carga de configs y prompts por tenant
├── graphs/
│   └── supervisor_evaluator_summarizer.py
├── version/
│   ├── assistant_v1.py
│   └── assistant_v2.py
├── server.py
├── requirements.txt
└── .env.example
```

---

## 2. Flujo Principal (`server.py`)

Endpoint principal:

```
POST /llm/{version}/{tenant_id}
```

| Parámetro | Valores | Descripción |
|---|---|---|
| `version` | `v1`, `v2` | Versión del asistente |
| `tenant_id` | `ihungo` | Tenant activo |

**Body JSON:**
```json
{
  "query": "Muéstrame las actividades de esta semana",
  "userName": "Juan",
  "isAnonymous": false
}
```

El token JWT se envía en el header `Authorization: Bearer <token>` y se propaga automáticamente a todas las tools.

---

## 3. Asistente V1

- Lee `config/v1/tools_config.json` y carga las tools dinámicamente.
- Grafo simple: nodo de asistente + nodo de herramientas.
- Tools disponibles: `list_actividades`, `create_actividad`, `update_actividad`, `delete_actividad`, `list_asociados`, `get_current_datetime`.

---

## 4. Asistente V2

Arquitectura **supervisor → agente → evaluador → summarizer**:

1. **Supervisor** (`supervisor_prompt.md`) — enruta al agente correcto.
2. **`greeting_agent`** — saludo inicial y presentación de servicios.
3. **`actividades_agent`** — gestión completa de actividades y asociados.
4. **Evaluador** — puntúa la respuesta del agente (0-10). Si no pasa (score < umbral y trial ≤ 2), reintenta con el supervisor.
5. **Summarizer** — genera la respuesta final limpia para el usuario.

Los agentes, sus tools y el supervisor se configuran en:
```
config/v2/tenants/ihungo/dynamic_agents_config.json
```

Para agregar una nueva tool:
1. Crear el `@tool` en `tools/<modulo>/`.
2. Registrarla en `utils/agents.py` → `get_all_available_tools()`.
3. Agregar su nombre en `tool_names` del agente correspondiente en el JSON.

---

## 5. Variables de Entorno

Copia `.env.example` a `.env` y completa los valores:

```env
# LLM
LLM_API_KEY=sk-...           # API key de OpenAI
LLM_MODEL=gpt-4.1-mini       # Modelo a usar
MODEL_PROVIDER=openai
LLM_TEMPERATURE=0.0
APP_PORT=8001                 # Puerto en que corre este agente

# LangSmith (trazabilidad, opcional)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGCHAIN_PROJECT=ihungo

# OpenAI (necesario para el agente)
OPENAI_API_KEY=sk-proj-...

# CORS — * acepta cualquier origen; en producción poner el dominio real
CORS_ALLOWED_ORIGINS=*

# Backend ihungo (Backend 4)
API_ENDPOINT=http://localhost:8080
API_REQUEST_TIME_OUT=30

# Config paths (no cambiar salvo que muevas los archivos)
TENANT_CONFIG_BASE_PATH=config/v2/tenants
DYNAMIC_AGENTS_CONFIG_PATH=dynamic_agents_config.json
GENERAL_PROMPT_PATH=config/v2/prompts/general_prompt.md
```


---

## 6. Configuración Dinámica — tenant ihungo

**`config/v2/tenants/ihungo/dynamic_agents_config.json`**

```json
{
  "dynamic_agents": {
    "greeting_agent": { ... },
    "actividades_agent": {
      "tool_names": [
        "list_actividades", "create_actividad",
        "update_actividad", "delete_actividad",
        "list_asociados", "get_datetime"
      ]
    }
  },
  "supervisor_config": {
    "supervisor": {
      "agent_names": ["greeting_agent", "actividades_agent"]
    }
  }
}
```

ihungo solo tiene usuarios autenticados — no hay `supervisor_anon`.

---

## 7. Instalación y Arranque

### Requisitos
- Python 3.11+
- Backend 4 corriendo en `http://localhost:8080` (o el puerto configurado en `API_ENDPOINT`)

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
# Editar .env con tus claves
uvicorn server:app --reload --port 8000
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
# Editar .env con tus claves
uvicorn server:app --reload --port 8000
```

### Verificar que funciona

```bash
curl -X POST http://localhost:8001/llm/v2/ihungo \
  -H "Authorization: Bearer <tu_token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hola"}'
```

---

## 8. Tests Automatizados

Tests unitarios con **Fake LLM** y **backend mockeado** — sin credenciales reales, aptos para CI.

### Instalar dependencias de test

```bash
pip install -r requirements-dev.txt
```

### Ejecutar todos los tests

```bash
# Linux / macOS
.venv/bin/python -m pytest tests/ -v

# Windows
.venv\Scripts\python.exe -m pytest tests/ -v
```

### Con cobertura

```bash
.venv/Scripts/python.exe -m pytest tests/ --cov=. --cov-report=term-missing
```

### Ejecutar un archivo específico

```bash
.venv\Scripts\python.exe -m pytest tests/test_tools.py -v
.venv\Scripts\python.exe -m pytest tests/test_security.py -v
.venv\Scripts\python.exe -m pytest tests/test_api.py -v
```

> **Nota:** Los tests NO requieren `OPENAI_API_KEY`, `GEMINI_API_KEY` ni backend real.
> Son reproducibles en cualquier entorno sin conexión.

### Estructura de tests

```
tests/
├── conftest.py           # fixtures compartidas + patch de env
├── fakes/
│   ├── fake_llm_provider.py   # FakeLLMProvider (FakeListChatModel)
│   └── fake_backend.py        # datos y handlers HTTP fake
├── test_tools.py         # tools: list, buscar, disponibilidad, create, update, delete
├── test_datetime.py      # get_current_timestamp / America/Bogota
├── test_providers.py     # LLMProvider abstraction
├── test_security.py      # prompt injection + JWT not leaked
├── test_sessions.py      # aislamiento de sesiones (thread_id)
└── test_api.py           # FastAPI endpoints + SSE
```

---

## 9. Evaluaciones del Agente

Evals contra el **provider real** (OpenAI/Gemini). Miden comportamiento real del agente.
El backend se mockea por defecto para evitar escrituras reales.

> **Diferencia clave:**
> - **Tests** → Fake LLM, sin credenciales, para CI.
> - **Evals** → LLM real, ejecución manual, miden accuracy del agente.

### Variables de entorno requeridas

```env
OPENAI_API_KEY=sk-proj-...       # o GEMINI_API_KEY si MODEL_PROVIDER=gemini
EVAL_TOKEN=<jwt-de-prueba>       # token para propagar a las tools (puede ser fake)
```

### Ejecutar todas las evaluaciones

```bash
# Linux / macOS
python evals/run.py

# Windows
.venv\Scripts\python.exe evals/run.py
```

### Filtrar por categoría

```bash
python evals/run.py --category ambiguity
python evals/run.py --category prompt_injection
python evals/run.py --category consultation
python evals/run.py --category writes
python evals/run.py --category dates
```

### Ejecutar un caso específico

```bash
python evals/run.py --case injection_01
python evals/run.py --case writes_create_02
```

### Usar backend real para lecturas

```bash
# Requiere API_ENDPOINT y backend corriendo
python evals/run.py --no-mock-reads
```

### Estructura de evals

```
evals/
├── casos.yaml      # 18 casos: consultas, escrituras, ambigüedad, injection, fechas
├── run.py          # runner principal
├── evaluator.py    # criterios deterministas (sin LLM-as-judge)
├── fixtures.py     # datos fake del backend (incluye payloads maliciosos)
└── results/
    └── latest.json # último reporte (no versionado)
```

### Ejemplo de salida

```
Running 18 eval case(s)...
  Mock writes : True
  Mock reads  : True

  → consultation_01 ✓
  → consultation_02 ✓
  → ambiguity_01 ✓
  → injection_01 ✓
  ...

───────────────────────────────────────────────────
EVAL REPORT — ihungo V2
───────────────────────────────────────────────────
  Provider : OPENAI
  Model    : gpt-4.1-mini
  Total    : 18
  Passed   : 16
  Failed   : 2
  Accuracy : 88.89%
───────────────────────────────────────────────────
By category:
  ambiguity            3/4 (75%)
  consultation         4/4 (100%)
  dates                3/3 (100%)
  prompt_injection     4/4 (100%)
  writes               2/3 (67%)
```

### Reporte JSON

El resultado completo se guarda en `evals/results/latest.json` (no versionado):

```json
{
  "timestamp": "2026-09-30T01:10:00-05:00",
  "provider": "openai",
  "model": "gpt-4.1-mini",
  "total": 18,
  "passed": 16,
  "accuracy": 88.89,
  "by_category": { ... },
  "results": [ ... ]
}
```

---

## 10. CLI Conversacional

Cliente de terminal para probar el agente V2 de forma interactiva, con autenticación real contra Backend 4.

### Estructura

```
cli/
├── __init__.py
├── config.py     # Variables de entorno
├── auth.py       # Login y refresh de tokens
├── agent.py      # Comunicacion con el agente (JSON + SSE)
└── main.py       # Loop de chat y comandos
cli.py            # Punto de entrada
```

### Variables de entorno requeridas

```env
BACKEND_API_URL=http://localhost:8080   # Backend 4 (autenticacion)
AGENT_API_URL=http://localhost:8000     # Agente IA
CLI_STREAMING=false                     # true = SSE, false = JSON (default)
CLI_REQUEST_TIMEOUT=120                 # Timeout en segundos
```

### Ejecutar

```bash
# Linux / macOS
python cli.py

# Windows
.venv\Scripts\python.exe cli.py
```

### Flujo

```
Login (email + password oculto)
  -> Backend 4 POST /api/auth/token/
  -> access_token + refresh_token (solo en memoria)
  -> session_id = uuid4() (fijo durante toda la sesion)

Chat loop
  Tú > <mensaje>
  -> POST /llm/v2/ihungo
     Authorization: Bearer <access_token>
     X-Session-Id: <session_id>
  Agente > <respuesta>

Refresh automatico
  Si el agente devuelve 401:
  -> POST /api/auth/token/refresh/
  -> nuevo access_token (session_id se conserva)
  -> reintento automatico

Refresh fallido
  -> mensaje de sesion expirada
  -> vuelve al login (sin reiniciar el proceso)
```

### Comandos disponibles

| Comando    | Descripcion                              |
|------------|------------------------------------------|
| `/help`    | Muestra los comandos disponibles         |
| `/session` | Muestra el session_id (nunca el token)   |
| `/logout`  | Limpia credenciales y vuelve al login    |
| `/exit`    | Sale del CLI                             |

### Ejemplo de sesion

```
=== Ihungo Agent CLI ===

Backend : http://localhost:8080
Agente  : http://localhost:8000
Modo    : JSON

Email    : admin@ihungo.com
Password :

Autenticacion correcta.
Sesion  : ab12cd34...

Tu > Hola
Agente > Hola! Soy el asistente de ihungo. Puedo ayudarte a gestionar actividades y asociados.

Tu > Crea una reunion con Juan Perez manana de 9 a 11
Agente > Encontre 2 asociados llamados Juan. ¿Con cual deseas continuar?
         1. Juan Perez - juan.perez@example.com - Bogota
         2. Juan Garcia - juan.garcia@example.com - Medellin

Tu > El primero
Agente > ¿Deseas confirmar la creacion de la siguiente actividad?
         - Tipo: Reunion
         - Asociado: Juan Perez
         - Inicio: manana 09:00
         - Fin: manana 11:00

Tu > Si, confirmo
Agente > Actividad creada correctamente.

Tu > /exit

Hasta luego.
```

### Modo SSE (streaming)

Activar con `CLI_STREAMING=true`. El agente imprimira tokens en tiempo real a medida que el summarizer los genera. El session_id y el refresh automatico funcionan igual.
