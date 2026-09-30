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
