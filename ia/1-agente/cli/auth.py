"""
cli/auth.py — Autenticacion y refresh de tokens contra Backend 4.

Tokens se mantienen unicamente en memoria.
Nunca se escriben en disco, logs ni stdout.
"""

import base64
import json as _json
import time
import httpx
from cli.config import BACKEND_API_URL, LOGIN_PATH, REFRESH_PATH, CLI_REQUEST_TIMEOUT

# Margen en segundos antes del vencimiento real para refrescar anticipadamente
_EXPIRY_MARGIN_SECONDS = 30


class AuthError(Exception):
    """Error de autenticacion controlado."""


def _decode_jwt_payload(token: str) -> dict:
    """Decodifica el payload del JWT sin verificar firma (solo para leer claims)."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        padding = 4 - len(parts[1]) % 4
        padded = parts[1] + "=" * padding
        payload = base64.urlsafe_b64decode(padded)
        return _json.loads(payload)
    except Exception:
        return {}


def is_token_expired(token: str) -> bool:
    """
    Verifica si el access token esta expirado o a punto de expirar.

    Lee el claim 'exp' del payload JWT sin verificar la firma.
    Aplica un margen de 30s para refrescar antes de que expire.

    Returns:
        True si el token debe refrescarse, False si todavia es valido.
    """
    payload = _decode_jwt_payload(token)
    exp = payload.get("exp")
    if not exp:
        # Sin claim exp: asumir valido, el backend decide
        return False
    return time.time() >= (exp - _EXPIRY_MARGIN_SECONDS)


def login(email: str, password: str) -> tuple[str, str, str]:
    """
    Autentica contra Backend 4.

    Returns:
        (access_token, refresh_token, user_name)
        user_name es el first_name del usuario si esta disponible,
        sino la parte del email antes del @.

    Raises:
        AuthError: credenciales invalidas o backend no disponible.
    """
    url = BACKEND_API_URL.rstrip("/") + LOGIN_PATH
    try:
        resp = httpx.post(
            url,
            json={"email": email, "password": password},
            timeout=CLI_REQUEST_TIMEOUT,
        )
    except httpx.ConnectError:
        raise AuthError("No fue posible conectar con el Backend 4. Verifica que este corriendo.")
    except httpx.TimeoutException:
        raise AuthError("El Backend 4 no respondio a tiempo.")

    if resp.status_code == 401:
        raise AuthError("Credenciales incorrectas.")
    if resp.status_code != 200:
        raise AuthError(f"Error de autenticacion (HTTP {resp.status_code}).")

    data = resp.json()
    access = data.get("access")
    refresh = data.get("refresh")
    if not access or not refresh:
        raise AuthError("Respuesta inesperada del servidor de autenticacion.")

    # Intentar obtener el nombre del usuario desde el payload del JWT
    payload = _decode_jwt_payload(access)
    user_name = (
        payload.get("first_name")
        or payload.get("name")
        or email.split("@")[0]
    )

    return access, refresh, user_name


def refresh_access_token(refresh_token: str) -> str:
    """
    Obtiene un nuevo access token usando el refresh token.

    Returns:
        Nuevo access_token.

    Raises:
        AuthError: refresh invalido/expirado o backend no disponible.
    """
    url = BACKEND_API_URL.rstrip("/") + REFRESH_PATH
    try:
        resp = httpx.post(
            url,
            json={"refresh": refresh_token},
            timeout=CLI_REQUEST_TIMEOUT,
        )
    except httpx.ConnectError:
        raise AuthError("No fue posible conectar con el Backend 4 para refrescar la sesion.")
    except httpx.TimeoutException:
        raise AuthError("El Backend 4 no respondio al intentar refrescar la sesion.")

    if resp.status_code in (401, 400):
        raise AuthError("La sesion de autenticacion expiro. Inicia sesion nuevamente.")
    if resp.status_code != 200:
        raise AuthError(f"Error al refrescar token (HTTP {resp.status_code}).")

    data = resp.json()
    new_access = data.get("access")
    if not new_access:
        raise AuthError("Respuesta inesperada al refrescar el token.")

    return new_access
