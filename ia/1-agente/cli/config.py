"""
cli/config.py — Configuracion del CLI leida desde variables de entorno.
"""

import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_API_URL: str = os.getenv("BACKEND_API_URL", "http://localhost:8080")
AGENT_API_URL: str = os.getenv("AGENT_API_URL", "http://localhost:8001")
CLI_STREAMING: bool = os.getenv("CLI_STREAMING", "false").lower() == "true"
CLI_REQUEST_TIMEOUT: float = float(os.getenv("CLI_REQUEST_TIMEOUT", "120"))

# Rutas de autenticacion (SimpleJWT)
LOGIN_PATH = "/api/auth/token/"
REFRESH_PATH = "/api/auth/token/refresh/"

# Ruta del agente V2
# FastAPI tiene root_path="/llm" que prefija todas las rutas
AGENT_PATH = "/llm/v2/ihungo"
AGENT_STREAM_PATH = "/llm/v2/ihungo/stream"
