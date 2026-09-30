# mcp_servers/base_tool.py
import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, Any
import os

from utils.request import api_request_manager_factory

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BaseToolConfigManager(ABC):
    _configs: Dict[str, Dict[str, Any]] = {}

    @classmethod
    async def get_tenant(cls, tenant_id: str) -> Dict[str, Any]:
        logger.debug(f"{cls.__name__}.get_tenant called for tenant: {tenant_id}")
        assert tenant_id is not None
        assert isinstance(tenant_id, str)
        assert isinstance(cls._configs, dict)

        if tenant_id not in cls._configs:
            logger.debug(
                f"Tenant '{tenant_id}' not in cache for {cls.__name__}, retrieving configuration."
            )
            try:
                specific_config = cls._build_specific_tenant_config(tenant_id)
                cls._configs[tenant_id] = specific_config
                logger.debug(
                    f"Tenant '{tenant_id}' configuration loaded and cached for {cls.__name__}."
                )
            except Exception as e:
                logger.error(
                    f"Failed to retrieve tenant '{tenant_id}' configuration for {cls.__name__}. {e}",
                    exc_info=True,
                )
                raise
        else:
            logger.debug(
                f"Tenant '{tenant_id}' configuration found in cache for {cls.__name__}."
            )
        return cls._configs[tenant_id]

    @staticmethod
    def build_env_config_dict() -> Dict[str, Any]:
        """
        Devuelve todas las variables de entorno en formato {'_nombre_variable': valor}, todo en minúsculas.
        """
        return {f"_{k.lower()}": v for k, v in os.environ.items()}

    @classmethod
    def _build_specific_tenant_config(cls, tenant_id: str = None) -> Dict[str, Any]:
        config = cls.build_env_config_dict()
        mgr = api_request_manager_factory()
        mgr.default_tenant_id = tenant_id
        config["_api_request_manager"] = mgr
        return config
