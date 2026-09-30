"""
cli/agent.py — Comunicacion con el agente V2 (JSON y SSE).

Maneja 401 con refresh automatico de token.
El session_id nunca cambia entre mensajes ni tras un refresh.
"""

import json
import httpx
from rich.console import Console
from rich.markdown import Markdown

_console = Console()


def print_agent(text: str) -> None:
    """Imprime la respuesta del agente renderizando Markdown."""
    _console.print("\n[bold cyan]Agente >[/bold cyan]")
    _console.print(Markdown(text))
    print()


from cli.config import (
    AGENT_API_URL,
    AGENT_PATH,
    AGENT_STREAM_PATH,
    CLI_REQUEST_TIMEOUT,
    CLI_STREAMING,
)
from cli.auth import refresh_access_token, is_token_expired, AuthError


class AgentError(Exception):
    """Error del agente controlado."""


class SessionExpiredError(Exception):
    """El refresh fallo — la sesion de autenticacion expiro."""


def _build_headers(access_token: str, session_id: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Session-Id": session_id,
        "Content-Type": "application/json",
    }


def _build_body(query: str, user_name: str) -> dict:
    return {
        "query": query,
        "language": "es",
        "userName": user_name,
        "isAnonymous": False,
    }


def send_message(
    query: str,
    access_token: str,
    refresh_token: str,
    session_id: str,
    user_name: str,
) -> tuple[str, str]:
    """
    Envia un mensaje al agente V2 (modo JSON).

    Realiza refresh automatico en 401 y reintenta una sola vez.

    Returns:
        (respuesta_texto, access_token_actual)
        El access_token puede haber cambiado si se refresco.

    Raises:
        AgentError: error del agente no recuperable.
        SessionExpiredError: refresh fallo, sesion expirada.
    """
    # Validacion proactiva: refrescar antes de que el token expire
    if is_token_expired(access_token):
        try:
            access_token = refresh_access_token(refresh_token)
        except AuthError as e:
            raise SessionExpiredError(str(e))

    url = AGENT_API_URL.rstrip("/") + AGENT_PATH

    def _do_request(token: str) -> httpx.Response:
        try:
            return httpx.post(
                url,
                headers=_build_headers(token, session_id),
                json=_build_body(query, user_name),
                timeout=CLI_REQUEST_TIMEOUT,
            )
        except httpx.ConnectError:
            raise AgentError("No fue posible conectar con el agente. Verifica que este corriendo.")
        except httpx.TimeoutException:
            raise AgentError("El agente no respondio a tiempo.")

    resp = _do_request(access_token)

    # Refresh automatico en 401
    if resp.status_code == 401:
        try:
            access_token = refresh_access_token(refresh_token)
        except AuthError as e:
            raise SessionExpiredError(str(e))
        resp = _do_request(access_token)

    if resp.status_code == 401:
        raise SessionExpiredError("La sesion de autenticacion expiro. Inicia sesion nuevamente.")

    if resp.status_code == 403:
        raise AgentError("No tienes permiso para realizar esta operacion.")
    if resp.status_code == 404:
        raise AgentError("Endpoint del agente no encontrado.")
    if resp.status_code >= 500:
        raise AgentError("Error interno del agente. Intenta de nuevo.")
    if resp.status_code != 200:
        raise AgentError(f"Error inesperado del agente (HTTP {resp.status_code}).")

    try:
        data = resp.json()
        response_text = data.get("response", "")
    except Exception:
        raise AgentError("Respuesta invalida del agente.")

    return response_text, access_token


def stream_message(
    query: str,
    access_token: str,
    refresh_token: str,
    session_id: str,
    user_name: str,
) -> tuple[str, str]:
    """
    Envia un mensaje al agente V2 usando SSE streaming.
    Imprime tokens en tiempo real y retorna la respuesta completa.

    Returns:
        (respuesta_completa, access_token_actual)

    Raises:
        AgentError, SessionExpiredError
    """
    # Validacion proactiva: refrescar antes de que el token expire
    if is_token_expired(access_token):
        try:
            access_token = refresh_access_token(refresh_token)
        except AuthError as e:
            raise SessionExpiredError(str(e))

    url = AGENT_API_URL.rstrip("/") + AGENT_STREAM_PATH
    headers = _build_headers(access_token, session_id)
    headers["Cache-Control"] = "no-cache"
    body = _build_body(query, user_name)

    def _do_stream(token: str) -> tuple[str, int]:
        """Returns (full_response, status_code)."""
        hdrs = _build_headers(token, session_id)
        hdrs["Cache-Control"] = "no-cache"
        full_parts: list[str] = []
        final_status = 200
        print("Agente > ", end="", flush=True)
        try:
            with httpx.stream(
                "POST",
                url,
                headers=hdrs,
                json=body,
                timeout=CLI_REQUEST_TIMEOUT,
            ) as resp:
                final_status = resp.status_code
                if final_status != 200:
                    resp.read()
                    return "", final_status

                for line in resp.iter_lines():
                    if not line:
                        continue
                    if line.startswith("event:"):
                        continue
                    if line.startswith("data:"):
                        raw = line[5:].strip()
                        try:
                            data = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        if "content" in data:
                            chunk = data["content"]
                            print(chunk, end="", flush=True)
                            full_parts.append(chunk)
                        elif "response" in data and not full_parts:
                            print(data["response"], end="", flush=True)
                            full_parts.append(data["response"])
        except httpx.ConnectError:
            raise AgentError("No fue posible conectar con el agente.")
        except httpx.TimeoutException:
            raise AgentError("El agente no respondio a tiempo.")

        print("\n")
        return "".join(full_parts), final_status

    full_response, status = _do_stream(access_token)

    if status == 401:
        try:
            access_token = refresh_access_token(refresh_token)
        except AuthError as e:
            raise SessionExpiredError(str(e))
        full_response, status = _do_stream(access_token)

    if status == 401:
        raise SessionExpiredError("La sesion de autenticacion expiro. Inicia sesion nuevamente.")
    if status == 403:
        raise AgentError("No tienes permiso para realizar esta operacion.")
    if status >= 500:
        raise AgentError("Error interno del agente.")
    if status != 200:
        raise AgentError(f"Error inesperado del agente (HTTP {status}).")

    return full_response, access_token


def send(
    query: str,
    access_token: str,
    refresh_token: str,
    session_id: str,
    user_name: str,
) -> tuple[str, str]:
    """
    Punto de entrada unico: delega a stream_message o send_message segun CLI_STREAMING.
    """
    if CLI_STREAMING:
        return stream_message(query, access_token, refresh_token, session_id, user_name)
    return send_message(query, access_token, refresh_token, session_id, user_name)
