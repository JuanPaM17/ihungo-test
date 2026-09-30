from typing import Annotated
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
    async def list_asociados(cls, tenant_id: str, token: str) -> list:
        tenant_config = await cls.get_tenant(tenant_id)
        basic_headers, _ = (
            tenant_config["_api_request_manager"].build_basic_info(token).values()
        )
        return await tenant_config["_api_request_manager"].make_request(
            method=HTTPMethod.GET,
            endpoint=cls._BASE_URL,
            headers=basic_headers,
            query_params=None,
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
