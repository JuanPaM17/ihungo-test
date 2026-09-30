import logging

import version.assistant_v2 as assistantV2
#from utils.tenant_config import get_tenant_config

logger = logging.getLogger(__name__)


async def clear_cache(tenant_id: str, version: str = "v2"):
    logger.info("Invalidating cache for tenant: %s", tenant_id)

    try:
        # Solo manejar versión v2
        if version.lower() != "v2":
            message = f"Version {version} is not supported. Only v2 is supported."
            logger.error(message)
            return {"status": "error", "message": message}

        assistantV2.assistant_manager.cache.clear()
        
        #await get_tenant_config.invalidate(tenant_id, version)

        logger.info(
            "Cache invalidated for tenant_id: %s, version: %s", tenant_id, version
        )
        return {"status": "success", "tenant_id": tenant_id, "version": version}

    except Exception as e:
        logger.error("Error invalidating cache: %s", str(e))
        return {"status": "error", "message": str(e)}
