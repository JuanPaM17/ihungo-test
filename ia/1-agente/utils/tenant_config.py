import logging
import json
from pathlib import Path
from utils.cached import cached
import os
from dotenv import load_dotenv
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv() 

def _resolve_base_path(env_name: str, default_value: str) -> Path:
    return Path(os.getenv(env_name, default_value))


def _tenant_root(tenant_id: str) -> Path:
    base_dir = _resolve_base_path("TENANT_CONFIG_BASE_PATH", "config/v2/tenants")
    return base_dir / tenant_id


def _resolve_tenant_path(tenant_id: str, relative_path: str) -> Path:
    return _tenant_root(tenant_id) / relative_path


_GLOBAL_PROMPTS = {
    "general_prompt.md",
    "evaluator_prompt.md",
    "summarizer_prompt.md",
}


def _resolve_global_prompt_path(name: str) -> Path:
    if name == "general_prompt.md":
        return _resolve_base_path(
            "GENERAL_PROMPT_PATH",
            "config/v2/prompts/general_prompt.md",
        )
    return Path(f"config/v2/prompts/{name}")

@cached(ttl=86400)
async def get_tenant_prompt(tenant_id: str, path: str):
    logger.debug("Retrieving %s the file from local", path)
    try:
        if not path:
            raise FileNotFoundError("Prompt path is required.")

        if path in _GLOBAL_PROMPTS:
            config_path = _resolve_global_prompt_path(path)
            prompt_path = str(config_path)
        else:
            relative_path = Path(path)
            prompt_path = str(_resolve_tenant_path(tenant_id, str(relative_path)))
            config_path = _resolve_tenant_path(tenant_id, str(relative_path))

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = f.read().replace("\r\n", "\n").strip()
        
        return config
    except Exception as e:
        logger.error(f"Error reading file from {path}: {e}")
        raise

def _load_json_from_local(tenant_id: str, tools_configuration_path: str) -> dict:
    """
    Gets a JSON file from the local file system for the requested tenant.

    Args:
        tenant_id: Tenant ID
        tools_configuration_path: Path to the base JSON file

    Returns:
        dict: Parsed JSON file content for the tenant
    """
    try:
        if not tools_configuration_path:
            tools_configuration_path = os.getenv(
                "DYNAMIC_AGENTS_CONFIG_PATH",
                "dynamic_agents_config.json",
            )

        config_path = Path(tools_configuration_path)
        if not config_path.is_absolute():
            config_path = _resolve_tenant_path(tenant_id, tools_configuration_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON from {tools_configuration_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading file from {tools_configuration_path}: {e}")
        raise

@cached(ttl=86400)
async def get_agent_prompt(tenant_id: str, name: str, prompt_type: str = "agent") -> Optional[str]:
    """
    Obtiene el prompt de un agente o sistema desde el sistema de archivos local.
    Args:
        tenant_id: ID del tenant
        name: Nombre del agente o sistema (ej: 'greeting_agent', 'supervisor', 'summarizer')
        prompt_type: 'agent' para agentes, 'supervisor' para supervisor, 'ocr' para OCR, 'system' para otros
    Returns:
        str | None: El contenido del prompt o None si no se encuentra
    """
    try:
        if name in _GLOBAL_PROMPTS:
            prompt_path = str(_resolve_global_prompt_path(name))
            prompt_content = await get_tenant_prompt(tenant_id, name)
        else:
            if prompt_type == "agent":
                prompt_path = str(Path("prompts") / "agents" / name)
            else:
                prompt_path = str(Path("prompts") / name)

            prompt_content = await get_tenant_prompt(tenant_id, prompt_path)

        if prompt_content is None:
            logger.error(f"No se pudo cargar el prompt para {name} desde {prompt_path}.")
            return None
        logger.info(f"Prompt para '{name}' cargado correctamente desde: {prompt_path}")
        return prompt_content
    except Exception as e:
        logger.error(f"Error obteniendo el prompt para {name}: {e}")
        return None

def get_json_from_local(tenant_id: str, tools_configuration_path: str) -> dict:
    return _load_json_from_local(tenant_id, tools_configuration_path)
