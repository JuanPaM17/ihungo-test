"""
cli/main.py — Loop principal del CLI conversacional.

Flujo:
  1. Mostrar banner y pedir credenciales.
  2. Login contra Backend 4.
  3. Generar session_id (uuid4, inmutable durante la sesion).
  4. Loop de chat: Tu > / Agente >
  5. Refresh automatico transparente en 401.
  6. Comandos: /help /session /logout /exit
"""

import getpass
import uuid

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

from cli.auth import login, AuthError
from cli.agent import send, print_agent, AgentError, SessionExpiredError
from cli.config import BACKEND_API_URL, AGENT_API_URL, CLI_STREAMING

_console = Console()

_COMMANDS = {
    "/help":    "Muestra esta ayuda.",
    "/session": "Muestra el ID de sesion actual.",
    "/logout":  "Cierra sesion y permite iniciar una nueva.",
    "/exit":    "Sale del CLI.",
}


def _send_with_spinner(
    query: str,
    access_token: str,
    refresh_token: str,
    session_id: str,
    user_name: str,
) -> tuple[str, str]:
    """
    Llama a send() mostrando un spinner animado mientras espera.
    En modo streaming el spinner se detiene cuando empiezan a llegar tokens.
    """
    result: list = []
    error: list = []

    if CLI_STREAMING:
        # En streaming el spinner no aplica — los tokens se imprimen en tiempo real
        return send(query, access_token, refresh_token, session_id, user_name)

    with _console.status("[dim]Pensando...[/dim]", spinner="dots"):
        try:
            response, new_token = send(query, access_token, refresh_token, session_id, user_name)
            result.append((response, new_token))
        except (AgentError, SessionExpiredError) as e:
            error.append(e)

    if error:
        raise error[0]
    return result[0]


def _banner():
    print()
    print("=== Ihungo Agent CLI ===")
    print()
    print(f"Backend : {BACKEND_API_URL}")
    print(f"Agente  : {AGENT_API_URL}")
    mode = "streaming (SSE)" if CLI_STREAMING else "JSON"
    print(f"Modo    : {mode}")
    print()


def _print_help():
    print()
    print("Comandos disponibles:")
    for cmd, desc in _COMMANDS.items():
        print(f"  {cmd:<12} {desc}")
    print()


def _do_login() -> tuple[str, str, str, str]:
    """
    Pide credenciales, autentica y retorna
    (access_token, refresh_token, session_id, user_name).
    """
    while True:
        email = input("Email    : ").strip()
        password = getpass.getpass("Password : ")
        if not email or not password:
            print("Email y password son requeridos.\n")
            continue
        try:
            access, refresh, user_name = login(email, password)
        except AuthError as e:
            print(f"\n{e}\n")
            continue

        session_id = str(uuid.uuid4())
        short_id = session_id[:8]
        print(f"\nAutenticacion correcta. Bienvenido, {user_name}.")
        print(f"Sesion  : {short_id}...\n")
        return access, refresh, session_id, user_name


def _handle_command(cmd: str, session_id: str) -> str:
    """
    Procesa un comando del CLI.

    Returns:
        "continue" | "logout" | "exit"
    """
    cmd = cmd.strip().lower()

    if cmd == "/help":
        _print_help()
        return "continue"

    if cmd == "/session":
        print(f"\nSesion activa : {session_id}\n")
        return "continue"

    if cmd == "/logout":
        print("\nSesion cerrada.\n")
        return "logout"

    if cmd == "/exit":
        print("\nHasta luego.\n")
        return "exit"

    # Comando desconocido — tratar como mensaje normal
    return "unknown"


def chat_loop(access_token: str, refresh_token: str, session_id: str, user_name: str) -> str:
    """
    Loop de conversacion.

    Returns:
        "logout" si el usuario ejecuto /logout
        "exit"   si el usuario ejecuto /exit o la sesion expiro sin posibilidad de recovery
    """
    # Saludo automatico al entrar al chat
    try:
        response, access_token = _send_with_spinner(
            query="Hola",
            access_token=access_token,
            refresh_token=refresh_token,
            session_id=session_id,
            user_name=user_name,
        )
        if not CLI_STREAMING:
            print_agent(response)
    except (AgentError, SessionExpiredError) as e:
        _console.print(f"[yellow][Aviso] No se pudo obtener saludo inicial: {e}[/yellow]\n")

    while True:
        try:
            user_input = input("Tú > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nHasta luego.\n")
            return "exit"

        if not user_input:
            continue

        # Comandos del CLI
        if user_input.startswith("/"):
            action = _handle_command(user_input, session_id)
            if action in ("logout", "exit"):
                return action
            if action == "continue":
                continue
            # "unknown" -> cae al envio normal (por si el usuario escribe "/" como mensaje)

        # Enviar al agente
        try:
            response, access_token = _send_with_spinner(
                query=user_input,
                access_token=access_token,
                refresh_token=refresh_token,
                session_id=session_id,
                user_name=user_name,
            )
            if not CLI_STREAMING:
                print_agent(response)

        except SessionExpiredError as e:
            _console.print(f"\n[red]{e}[/red]\n")
            return "logout"

        except AgentError as e:
            _console.print(f"\n[red][Error] {e}[/red]\n")
            # No salir — el usuario puede seguir intentando


def run():
    """Punto de entrada principal del CLI."""
    _banner()

    while True:
        access_token, refresh_token, session_id, user_name = _do_login()

        action = chat_loop(access_token, refresh_token, session_id, user_name)

        # Limpiar tokens de memoria explicitamente
        del access_token
        del refresh_token

        if action == "exit":
            break
        # action == "logout" -> vuelve al login
        print("Inicia sesion nuevamente.\n")
