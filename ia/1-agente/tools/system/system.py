import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.debug("Starting: System Agent")

# Langchain
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

# Multi-tenancy
from utils.date_time import get_current_timestamp
from tools.base_tool import BaseToolConfigManager
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
#from utils.tenant_config import invalidate_all_prompts_cache


class SystemTool(BaseToolConfigManager):
    _BASE_URL = "system"

    @classmethod
    async def invalidate_cache(cls, tenant_id: str, version: str) -> dict:
        """Invalidate cache for the tenant"""
        from utils.invalidate_cache import clear_cache
        logger.debug(f'invalidate_cache: {tenant_id} - {version}')
        try:
            logger.info(f"Invalidating cache for tenant: {tenant_id}")
            result = await clear_cache(tenant_id, version)
            logger.info(f"Response: {result}")
            #await invalidate_all_prompts_cache(tenant_id)
            logger.info(f"Prompt cache invalidated for tenant: {tenant_id}")
            return result
        except Exception as e:
            logger.error(f"Error during invalidate_cache for tenant '{tenant_id}': {e}", exc_info=True)
            raise

    @classmethod
    async def get_datetime(cls, tenant_id: str, token: str) -> str:
        """Get current date and time"""
        logger.debug(f'get_datetime: {tenant_id}')
        tenant_config = await cls.get_tenant(tenant_id)
        logger.debug(tenant_id)
        logger.debug(tenant_config)
        assert tenant_config is not None, f'tenant_config={tenant_config}'
        assert isinstance(tenant_config, dict)
        try:
            result = get_current_timestamp()
            logger.info(f"Response: {result}")
            return result
        except Exception as e:
            logger.error(f"Error during get_datetime for tenant '{tenant_id}': {e}", exc_info=True)
            raise


@tool
async def invalidate_cache(
    config: RunnableConfig,
) -> dict:
    """Invalidate cache for the current tenant."""
    logger.debug("INVALIDATE_CACHE")
    metadata = config.get('metadata')
    configurable = config.get('configurable', {})
    
    if metadata is None:
        raise ValueError("metadata is None")
    
    # Get tenant_id from configurable (where it's actually stored)
    tenant_id = configurable.get("tenant_id")
    logger.debug(f"{tenant_id}")
    if not tenant_id:
        raise ValueError("tenant_id must be provided in the config.configurable!")
    
    version = configurable.get("version")
    logger.debug(f"{version}")
    if not version:
        raise ValueError("version must be provided in the config.version!")

    results = await SystemTool.invalidate_cache(tenant_id=tenant_id, version=version)
    return results

@tool
async def get_datetime(
    config: RunnableConfig,
) -> dict:
    """
    Returns the current date and time in America/Bogota timezone as a structured object.

    Use this tool ALWAYS before resolving any relative date expression
    (hoy, mañana, pasado mañana, próximo lunes, esta semana, etc.).
    Never calculate dates from your training knowledge — always call this tool first.

    Returned fields:
    - timezone: always "America/Bogota"
    - datetime: full ISO 8601 with offset, e.g. "2026-09-30T23:55:00-05:00"
    - date: "2026-09-30"
    - time: "23:55:00"
    - day_of_week: e.g. "Wednesday"
    - utc_offset: e.g. "-05:00"
    """
    logger.debug("GET_DATETIME")
    configurable = config.get("configurable") or {}
    tenant_id = configurable.get("tenant_id")
    token = configurable.get("token")
    logger.debug(f"{tenant_id}")
    if not tenant_id or not token:
        raise ValueError("tenant_id and token must be provided in config.configurable")

    results = await SystemTool.get_datetime(tenant_id=tenant_id, token=token)
    return results
