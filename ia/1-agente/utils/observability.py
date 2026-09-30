"""
Observabilidad estructurada local para el agente V2.

Registra una línea JSONL por turno en logs/agent.jsonl con:
  timestamp, session_id, provider, model, tools_called,
  latency_ms, input_tokens, output_tokens, iterations, status, error

NO se registra: JWT, Authorization, API keys, prompts completos,
contenido de ToolMessage, datos personales del usuario.

Relación con LangSmith: complementaria. LangSmith captura trazas
detalladas en la nube; este archivo captura métricas locales por turno
sin depender de conectividad externa.

Concurrencia: asyncio.Lock garantiza que líneas de requests concurrentes
no se mezclen en el archivo.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from langchain_core.messages import AIMessage, ToolMessage

logger = logging.getLogger(__name__)

# ── Archivo de salida ──────────────────────────────────────────────────────────
_LOG_DIR = Path(__file__).parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "agent.jsonl"

# ── Lock para escritura concurrente segura ─────────────────────────────────────
_write_lock = asyncio.Lock()

# ── Info del proveedor (leída una sola vez al importar) ───────────────────────
_PROVIDER = os.getenv("MODEL_PROVIDER", "openai").lower()
_MODEL = os.getenv("OPENAI_MODEL", "") or os.getenv("GEMINI_MODEL", "") or "unknown"


def _ensure_log_dir() -> None:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)


def _bogota_timestamp() -> str:
    """ISO 8601 con offset America/Bogota (-05:00)."""
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(tz=ZoneInfo("America/Bogota"))
    except Exception:
        now = datetime.utcnow()
    offset = now.strftime("%z")
    if offset:
        utc_offset = f"{offset[:3]}:{offset[3:]}"
        return now.strftime(f"%Y-%m-%dT%H:%M:%S{utc_offset}")
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def extract_metrics_from_messages(messages: list, turn_start_index: int) -> dict:
    """
    Extrae métricas del turno actual a partir de los mensajes nuevos
    (desde turn_start_index hasta el final).

    Returns:
        {
            "tools_called": [...],
            "input_tokens": int | None,
            "output_tokens": int | None,
            "iterations": int,
        }
    """
    turn_messages = messages[turn_start_index:] if turn_start_index < len(messages) else messages

    tools_called: list[str] = []
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    iterations = 0

    for msg in turn_messages:
        # Tool names — solo el nombre, nunca los argumentos
        if isinstance(msg, ToolMessage) and msg.name:
            tools_called.append(msg.name)

        # Token usage — sumar todos los AIMessage del turno
        if isinstance(msg, AIMessage):
            iterations += 1
            usage = getattr(msg, "usage_metadata", None)
            if usage:
                in_t = usage.get("input_tokens") or usage.get("prompt_tokens")
                out_t = usage.get("output_tokens") or usage.get("completion_tokens")
                if in_t is not None:
                    input_tokens = (input_tokens or 0) + int(in_t)
                if out_t is not None:
                    output_tokens = (output_tokens or 0) + int(out_t)

    return {
        "tools_called": tools_called,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "iterations": iterations,
    }


async def write_turn_log(
    session_id: str,
    latency_ms: int,
    status: str,
    messages: list = None,
    turn_start_index: int = 0,
    error: Optional[str] = None,
) -> None:
    """
    Escribe una línea JSONL en logs/agent.jsonl para el turno actual.

    Args:
        session_id:        Identificador de sesión (no JWT).
        latency_ms:        Latencia total del turno en milisegundos.
        status:            "success" | "error" | "cancelled".
        messages:          Lista completa de mensajes del estado final.
        turn_start_index:  Índice desde el que empiezan los mensajes del turno.
        error:             Mensaje de error corto (sin stacktrace).
    """
    _ensure_log_dir()

    metrics: dict = {"tools_called": [], "input_tokens": None, "output_tokens": None, "iterations": 0}
    if messages:
        try:
            metrics = extract_metrics_from_messages(messages, turn_start_index)
        except Exception as exc:
            logger.warning("observability: could not extract metrics: %s", exc)

    record = {
        "timestamp": _bogota_timestamp(),
        "session_id": session_id,
        "provider": _PROVIDER,
        "model": _MODEL,
        "tools_called": metrics["tools_called"],
        "latency_ms": latency_ms,
        "input_tokens": metrics["input_tokens"],
        "output_tokens": metrics["output_tokens"],
        "iterations": metrics["iterations"],
        "status": status,
        "error": error,
    }

    line = json.dumps(record, ensure_ascii=False)

    async with _write_lock:
        try:
            with open(_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as exc:
            logger.error("observability: failed to write log: %s", exc)
