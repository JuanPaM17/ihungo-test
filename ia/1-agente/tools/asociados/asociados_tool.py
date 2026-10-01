from typing import Annotated, Optional
import logging
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from tools.base_tool import BaseToolConfigManager
from utils.request import HTTPMethod

logger = logging.getLogger(__name__)

BASE_URL = "api/asociados"


class AsociadoTool(BaseToolConfigManager):
    _BASE_URL = BASE_URL

    @classmethod
    async def list_asociados(cls, tenant_id: str, token: str, params: dict | None = None) -> list:
        tenant_config = await cls.get_tenant(tenant_id)
        basic_headers, _ = (
            tenant_config["_api_request_manager"].build_basic_info(token).values()
        )
        return await tenant_config["_api_request_manager"].make_request(
            method=HTTPMethod.GET,
            endpoint=cls._BASE_URL,
            headers=basic_headers,
            query_params=params or {},
            body_params=None,
        )

    @classmethod
    async def get_asociado(cls, tenant_id: str, token: str, asociado_id: int) -> dict:
        tenant_config = await cls.get_tenant(tenant_id)
        basic_headers, _ = (
            tenant_config["_api_request_manager"].build_basic_info(token).values()
        )
        return await tenant_config["_api_request_manager"].make_request(
            method=HTTPMethod.GET,
            endpoint=f"{cls._BASE_URL}/{asociado_id}/",
            headers=basic_headers,
            query_params={},
            body_params=None,
        )

    @classmethod
    async def create_asociado(cls, tenant_id: str, token: str, body: dict) -> dict:
        tenant_config = await cls.get_tenant(tenant_id)
        basic_headers, _ = (
            tenant_config["_api_request_manager"].build_basic_info(token).values()
        )
        return await tenant_config["_api_request_manager"].make_request(
            method=HTTPMethod.POST,
            endpoint=cls._BASE_URL + "/",
            headers=basic_headers,
            query_params={},
            body_params=body,
        )

    @classmethod
    async def update_asociado(cls, tenant_id: str, token: str, asociado_id: int, body: dict) -> dict:
        tenant_config = await cls.get_tenant(tenant_id)
        basic_headers, _ = (
            tenant_config["_api_request_manager"].build_basic_info(token).values()
        )
        return await tenant_config["_api_request_manager"].make_request(
            method=HTTPMethod.PATCH,
            endpoint=f"{cls._BASE_URL}/{asociado_id}/",
            headers=basic_headers,
            query_params={},
            body_params=body,
        )

    @classmethod
    async def delete_asociado(cls, tenant_id: str, token: str, asociado_id: int) -> dict:
        tenant_config = await cls.get_tenant(tenant_id)
        basic_headers, _ = (
            tenant_config["_api_request_manager"].build_basic_info(token).values()
        )
        return await tenant_config["_api_request_manager"].make_request(
            method=HTTPMethod.DELETE,
            endpoint=f"{cls._BASE_URL}/{asociado_id}/",
            headers=basic_headers,
            query_params={},
            body_params=None,
        )


def _get_metadata(config: RunnableConfig) -> tuple[str, str]:
    configurable = config.get("configurable") or {}
    tenant_id = configurable.get("tenant_id")
    token = configurable.get("token")
    if not tenant_id or not token:
        raise ValueError("tenant_id and token must be provided in config.configurable")
    return tenant_id, token


@tool
async def list_asociados(config: RunnableConfig) -> list:
    """
    Lista todos los asociados registrados en el sistema.

    No requiere parámetros adicionales.

    Respuesta exitosa:
    - Lista de asociados con id, email, identificación, nombre, apellido y ciudad.

    Respuesta sin resultados:
    - Lista vacía [].

    Ejemplos de consulta:
    - "¿Cuáles son los asociados disponibles?"
    - "Muéstrame todos los asociados."
    - "Lista los asociados para asignar una actividad."
    """
    tenant_id, token = _get_metadata(config)
    return await AsociadoTool.list_asociados(tenant_id=tenant_id, token=token)


@tool
async def buscar_asociados(
    config: RunnableConfig,
    nombre: Annotated[Optional[str], "Nombre o apellido (parcial, case-insensitive). Ejemplo: 'Juan' o 'Pérez'."] = None,
    email: Annotated[Optional[str], "Email o parte del email del asociado. Ejemplo: 'juan@'."] = None,
    ciudad: Annotated[Optional[str], "Ciudad del asociado (parcial, case-insensitive). Ejemplo: 'Bogotá'."] = None,
    identificacion: Annotated[Optional[str], "Número de identificación del asociado (parcial). Ejemplo: '123456'."] = None,
) -> dict:
    """
    Busca asociados usando filtros soportados por el backend.

    Filtros disponibles (todos opcionales, al menos uno recomendado):
    - nombre: busca en first_name + last_name (coincidencia parcial, case-insensitive).
    - email: busca en el email (coincidencia parcial).
    - ciudad: busca en el campo city (coincidencia parcial).
    - identificacion: busca en el campo identification (coincidencia parcial).

    Respuesta:
    - total: número de coincidencias encontradas.
    - coincidencias: lista de asociados (id, email, identification, first_name, last_name, city).
    - mensaje: descripción del resultado.

    Ejemplos de consulta:
    - "Busca al asociado Juan Pérez."
    - "¿Hay algún asociado en Medellín?"
    - "Encuentra al asociado con email maria@."
    """
    tenant_id, token = _get_metadata(config)

    if not any([nombre, email, ciudad, identificacion]):
        return {
            "total": 0,
            "coincidencias": [],
            "mensaje": "Debes proporcionar al menos un filtro de búsqueda (nombre, email, ciudad o identificacion).",
        }

    params = {}
    if nombre:
        params["nombre"] = nombre
    if email:
        params["email"] = email
    if ciudad:
        params["ciudad"] = ciudad
    if identificacion:
        params["identificacion"] = identificacion

    raw = await AsociadoTool.list_asociados(tenant_id=tenant_id, token=token, params=params)

    if isinstance(raw, dict) and "error" in raw:
        return {"total": 0, "coincidencias": [], "mensaje": f"Error al consultar asociados: {raw['error']}"}

    if not isinstance(raw, list):
        return {"total": 0, "coincidencias": [], "mensaje": "Respuesta inesperada del servidor."}

    total = len(raw)
    if total == 0:
        mensaje = "No se encontraron asociados con los filtros indicados."
    elif total == 1:
        mensaje = "Se encontró 1 asociado."
    else:
        mensaje = f"Se encontraron {total} asociados."

    return {"total": total, "coincidencias": raw, "mensaje": mensaje}


@tool
async def obtener_asociado(
    config: RunnableConfig,
    asociado_id: Annotated[int, "ID numérico del asociado a consultar."],
) -> dict:
    """
    Obtiene el detalle de un asociado específico por su ID.

    Parámetros:
    - asociado_id: ID numérico del asociado.

    Respuesta exitosa:
    - id, email, identification, first_name, last_name, city, created_at.

    Errores:
    - 404 si el asociado no existe.

    Ejemplos de consulta:
    - "Muéstrame el detalle del asociado 3."
    - "¿Cuál es la información del asociado con ID 7?"
    """
    tenant_id, token = _get_metadata(config)
    return await AsociadoTool.get_asociado(tenant_id=tenant_id, token=token, asociado_id=asociado_id)


@tool
async def crear_asociado(
    config: RunnableConfig,
    email: Annotated[str, "Email del nuevo asociado. Debe ser único."],
    password: Annotated[str, "Contraseña inicial del asociado."],
    identification: Annotated[str, "Número de identificación (cédula). Debe ser único."],
    first_name: Annotated[str, "Nombre del asociado."],
    last_name: Annotated[str, "Apellido del asociado."],
    city: Annotated[str, "Ciudad del asociado."],
) -> dict:
    """
    Crea un nuevo asociado en el sistema. Requiere rol administrador.

    Parámetros obligatorios:
    - email, password, identification, first_name, last_name, city.

    Respuesta exitosa:
    - Datos del asociado creado (id, email, first_name, last_name, city, identification, created_at).

    Errores:
    - 400 si el email o la identificación ya existen.
    - 403 si el usuario autenticado no es administrador.

    Ejemplos de consulta:
    - "Crea un asociado llamado María Torres con email maria@example.com."
    - "Registra un nuevo asociado: Juan López, identificación 123456, ciudad Bogotá."

    IMPORTANTE: Siempre solicitar confirmación antes de ejecutar esta herramienta.
    """
    tenant_id, token = _get_metadata(config)

    if not password or not str(password).strip():
        return {
            "success": False,
            "action": "create_associate",
            "error": "El campo 'password' es obligatorio y no puede estar vacío. Solicita una contraseña al usuario antes de continuar.",
        }

    body = {
        "email": email,
        "password": password,
        "identification": identification,
        "first_name": first_name,
        "last_name": last_name,
        "city": city,
    }
    safe_keys = [k for k in body if k != "password"]
    logger.info("crear_asociado: method=POST endpoint=/api/asociados/ payload_keys=%s", safe_keys)
    result = await AsociadoTool.create_asociado(tenant_id=tenant_id, token=token, body=body)

    # Detect redirect/wrong response: backend returned a list instead of a dict
    if isinstance(result, list):
        logger.error("crear_asociado: received a list instead of a dict — likely a redirect on POST (missing trailing slash)")
        return {"success": False, "action": "create_associate", "error": "El servidor devolvió una respuesta inesperada. No se pudo confirmar la creación."}

    if isinstance(result, dict):
        # Error from backend (400, 403, 409, etc.)
        if "error" in result or "detail" in result:
            return {"success": False, "action": "create_associate", "error": result.get("error") or result.get("detail")}
        # Success: backend returns the created asociado with an id field
        if "id" in result:
            return {"success": True, "action": "create_associate", "status_code": 201, "data": result}

    return {"success": False, "action": "create_associate", "error": f"Respuesta inesperada: {result}"}


@tool
async def actualizar_asociado(
    config: RunnableConfig,
    asociado_id: Annotated[int, "ID numérico del asociado a modificar."],
    first_name: Annotated[Optional[str], "Nuevo nombre. Omitir si no cambia."] = None,
    last_name: Annotated[Optional[str], "Nuevo apellido. Omitir si no cambia."] = None,
    city: Annotated[Optional[str], "Nueva ciudad. Omitir si no cambia."] = None,
    identification: Annotated[Optional[str], "Nueva identificación. Omitir si no cambia."] = None,
    email: Annotated[Optional[str], "Nuevo email. Omitir si no cambia."] = None,
) -> dict:
    """
    Actualiza parcialmente los datos de un asociado. Requiere rol administrador.

    Parámetros:
    - asociado_id: ID del asociado (obligatorio).
    - Enviar solo los campos que deben cambiar.

    Respuesta exitosa:
    - Datos actualizados del asociado.

    Errores:
    - 400 si el email o identificación ya pertenecen a otro usuario.
    - 403 si el usuario autenticado no es administrador.
    - 404 si el asociado no existe.

    Ejemplos de consulta:
    - "Cambia la ciudad del asociado 5 a Medellín."
    - "Actualiza el apellido del asociado 3 a 'Ramírez'."

    IMPORTANTE: Siempre solicitar confirmación antes de ejecutar esta herramienta.
    """
    tenant_id, token = _get_metadata(config)
    body = {}
    if first_name is not None:
        body["first_name"] = first_name
    if last_name is not None:
        body["last_name"] = last_name
    if city is not None:
        body["city"] = city
    if identification is not None:
        body["identification"] = identification
    if email is not None:
        body["email"] = email

    if not body:
        return {"error": "Debes proporcionar al menos un campo para actualizar."}

    return await AsociadoTool.update_asociado(
        tenant_id=tenant_id, token=token, asociado_id=asociado_id, body=body
    )


@tool
async def eliminar_asociado(
    config: RunnableConfig,
    asociado_id: Annotated[int, "ID numérico del asociado a eliminar."],
) -> dict:
    """
    Elimina un asociado del sistema. Requiere rol administrador.

    Parámetros:
    - asociado_id: ID numérico del asociado.

    Respuesta exitosa:
    - Confirmación de eliminación.

    Errores:
    - 403 si el usuario autenticado no es administrador.
    - 404 si el asociado no existe.
    - 409 si el asociado tiene actividades asociadas (eliminar primero las actividades).

    Ejemplos de consulta:
    - "Elimina al asociado con ID 4."
    - "Borra el perfil del asociado 7."

    IMPORTANTE: Esta acción es irreversible. Siempre solicitar confirmación explícita antes de ejecutar.
    """
    tenant_id, token = _get_metadata(config)
    result = await AsociadoTool.delete_asociado(
        tenant_id=tenant_id, token=token, asociado_id=asociado_id
    )
    # 204 No Content → make_request devuelve "" (string vacío) = éxito
    if not result:
        return {"eliminado": True, "asociado_id": asociado_id}
    # 409 HAS_ACTIVITIES → make_request captura raise_for_status() y devuelve {"error": "...409..."}
    # También puede llegar como {"code": "HAS_ACTIVITIES", "detail": "..."} si el body fue parseado
    if isinstance(result, dict):
        code = result.get("code", "")
        error_str = str(result.get("error", ""))
        if code == "HAS_ACTIVITIES" or "409" in error_str:
            return {
                "error": "HAS_ACTIVITIES",
                "mensaje": (
                    "No se puede eliminar el asociado porque tiene actividades asociadas. "
                    "Debes eliminar primero todas sus actividades y luego intentar de nuevo."
                ),
            }
    return result
