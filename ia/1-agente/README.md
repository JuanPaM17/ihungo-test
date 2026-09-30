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
