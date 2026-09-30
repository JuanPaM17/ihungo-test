from typing import Optional, Annotated
import logging
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from tools.base_tool import BaseToolConfigManager
from utils.request import HTTPMethod

logger = logging.getLogger(__name__)

BASE_URL = "api/actividades"


class ActividadTool(BaseToolConfigManager):
    _BASE_URL = BASE_URL

    @classmethod
    async def list_actividades(cls, tenant_id: str, token: str, params: dict) -> list:
        tenant_config = await cls.get_tenant(tenant_id)
        basic_headers, _ = (
            tenant_config["_api_request_manager"].build_basic_info(token).values()
        )
        return await tenant_config["_api_request_manager"].make_request(
            method=HTTPMethod.GET,
            endpoint=cls._BASE_URL,
            headers=basic_headers,
            query_params=params,
            body_params=None,
        )

    @classmethod
    async def create_actividad(cls, tenant_id: str, token: str, body: dict) -> dict:
        tenant_config = await cls.get_tenant(tenant_id)
        basic_headers, _ = (
            tenant_config["_api_request_manager"].build_basic_info(token).values()
        )
        return await tenant_config["_api_request_manager"].make_request(
            method=HTTPMethod.POST,
            endpoint=cls._BASE_URL,
            headers=basic_headers,
            query_params=None,
            body_params=body,
        )

    @classmethod
    async def update_actividad(cls, tenant_id: str, token: str, actividad_id: int, body: dict) -> dict:
        tenant_config = await cls.get_tenant(tenant_id)
        basic_headers, _ = (
            tenant_config["_api_request_manager"].build_basic_info(token).values()
        )
        return await tenant_config["_api_request_manager"].make_request(
            method=HTTPMethod.PATCH,
            endpoint=f"{cls._BASE_URL}/{actividad_id}",
            headers=basic_headers,
            query_params=None,
            body_params=body,
        )

    @classmethod
    async def delete_actividad(cls, tenant_id: str, token: str, actividad_id: int) -> dict:
        tenant_config = await cls.get_tenant(tenant_id)
        basic_headers, _ = (
            tenant_config["_api_request_manager"].build_basic_info(token).values()
        )
        return await tenant_config["_api_request_manager"].make_request(
            method=HTTPMethod.DELETE,
            endpoint=f"{cls._BASE_URL}/{actividad_id}",
            headers=basic_headers,
            query_params=None,
            body_params=None,
        )


# ── Tool helpers ────────────────────────────────────────────────────────────

def _get_metadata(config: RunnableConfig) -> tuple[str, str]:
    configurable = config.get("configurable") or {}
    tenant_id = configurable.get("tenant_id")
    token = configurable.get("token")
    if not tenant_id or not token:
        raise ValueError("tenant_id and token must be provided in config.configurable")
    return tenant_id, token


# ── Tools ────────────────────────────────────────────────────────────────────

@tool
async def list_actividades(
    config: RunnableConfig,
    desde: Annotated[Optional[str], Field(description="Fecha/datetime de inicio del rango (ISO 8601). Ejemplo: 2025-01-01 o 2025-01-01T00:00:00Z")] = None,
    hasta: Annotated[Optional[str], Field(description="Fecha/datetime de fin del rango (ISO 8601). Ejemplo: 2025-12-31 o 2025-12-31T23:59:59Z")] = None,
) -> list:
    """
    Lista las actividades registradas en el sistema.

    Parámetros opcionales:
    - desde: filtra actividades cuyo start_datetime >= este valor.
    - hasta: filtra actividades cuyo start_datetime <= este valor.

    Respuesta exitosa:
    - Lista de actividades con id, tipo, descripción, fechas, asociado y creador.

    Respuesta sin resultados:
    - Lista vacía [].

    Ejemplos de consulta:
    - "Muéstrame las actividades de enero 2025."
    - "¿Qué actividades hay esta semana?"
    - "Lista todas las actividades."
    """
    tenant_id, token = _get_metadata(config)
    params = {}
    if desde:
        params["desde"] = desde
    if hasta:
        params["hasta"] = hasta
    return await ActividadTool.list_actividades(tenant_id=tenant_id, token=token, params=params)


@tool
async def create_actividad(
    config: RunnableConfig,
    activity_type: Annotated[str, Field(description="Tipo de actividad. Valores válidos: workshop, seminar, meeting, training, other")],
    start_datetime: Annotated[str, Field(description="Fecha y hora de inicio en formato ISO 8601. Ejemplo: 2025-03-10T09:00:00Z")],
    end_datetime: Annotated[str, Field(description="Fecha y hora de fin en formato ISO 8601. Ejemplo: 2025-03-10T11:00:00Z")],
    asociado: Annotated[int, Field(description="ID numérico del asociado al que pertenece la actividad")],
    description: Annotated[Optional[str], Field(description="Descripción o notas adicionales de la actividad")] = "",
) -> dict:
    """
    Crea una nueva actividad en el sistema.

    Campos requeridos:
    - activity_type: tipo de actividad (workshop, seminar, meeting, training, other).
    - start_datetime: fecha y hora de inicio (ISO 8601).
    - end_datetime: fecha y hora de fin (ISO 8601).
    - asociado: ID del asociado.

    Campos opcionales:
    - description: descripción o notas.

    Respuesta exitosa (201):
    - Objeto de la actividad creada con todos sus campos.

    Respuesta de error:
    - 409 si la actividad genera solapamiento de horario para ese asociado.
    - 400 si los datos son inválidos.

    Ejemplos de consulta:
    - "Crea un taller para el asociado 3 el 15 de marzo de 9 a 11."
    - "Registra una reunión para mañana con el asociado 5."
    """
    tenant_id, token = _get_metadata(config)
    body = {
        "activity_type": activity_type,
        "description": description,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "asociado": asociado,
    }
    return await ActividadTool.create_actividad(tenant_id=tenant_id, token=token, body=body)


@tool
async def update_actividad(
    config: RunnableConfig,
    actividad_id: Annotated[int, Field(description="ID numérico de la actividad a modificar")],
    activity_type: Annotated[Optional[str], Field(description="Nuevo tipo de actividad: workshop, seminar, meeting, training, other")] = None,
    start_datetime: Annotated[Optional[str], Field(description="Nueva fecha y hora de inicio (ISO 8601)")] = None,
    end_datetime: Annotated[Optional[str], Field(description="Nueva fecha y hora de fin (ISO 8601)")] = None,
    asociado: Annotated[Optional[int], Field(description="Nuevo ID del asociado")] = None,
    description: Annotated[Optional[str], Field(description="Nueva descripción")] = None,
) -> dict:
    """
    Modifica parcialmente una actividad existente (PATCH).

    Solo envía los campos que deban cambiar; los demás se conservan.

    Parámetros:
    - actividad_id: ID de la actividad a modificar (requerido).
    - activity_type, start_datetime, end_datetime, asociado, description: opcionales.

    Respuesta exitosa:
    - Objeto de la actividad con los datos actualizados.

    Respuesta de error:
    - 409 si el cambio genera solapamiento de horario.
    - 404 si la actividad no existe.

    Ejemplos de consulta:
    - "Cambia la hora de inicio de la actividad 7 a las 10am."
    - "Actualiza la descripción de la actividad 12."
    """
    tenant_id, token = _get_metadata(config)
    body = {}
    if activity_type is not None:
        body["activity_type"] = activity_type
    if start_datetime is not None:
        body["start_datetime"] = start_datetime
    if end_datetime is not None:
        body["end_datetime"] = end_datetime
    if asociado is not None:
        body["asociado"] = asociado
    if description is not None:
        body["description"] = description
    return await ActividadTool.update_actividad(tenant_id=tenant_id, token=token, actividad_id=actividad_id, body=body)


@tool
async def delete_actividad(
    config: RunnableConfig,
    actividad_id: Annotated[int, Field(description="ID numérico de la actividad a eliminar")],
) -> dict:
    """
    Elimina una actividad del sistema de forma permanente.

    Parámetros:
    - actividad_id: ID de la actividad a eliminar (requerido).

    Respuesta exitosa:
    - Confirmación de eliminación (204 sin contenido).

    Respuesta de error:
    - 404 si la actividad no existe.
    - 403 si el usuario no tiene permiso para eliminarla.

    Ejemplos de consulta:
    - "Borra la actividad 9."
    - "Elimina la actividad con ID 4."
    """
    tenant_id, token = _get_metadata(config)
    return await ActividadTool.delete_actividad(tenant_id=tenant_id, token=token, actividad_id=actividad_id)
