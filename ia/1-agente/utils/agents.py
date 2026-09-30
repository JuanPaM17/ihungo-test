import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from dotenv import load_dotenv

load_dotenv()

async def get_dynamic_prompt(
    tenant_id: str,
    agent_name: str,
    state: dict | None = None,
    prompt_type: str = "agent",
) -> str:
    """Get dynamic prompt from S3 configuration."""
    if not tenant_id:
        return None

    try:
        from utils.tenant_config import get_agent_prompt

        prompt = await get_agent_prompt(tenant_id, agent_name, prompt_type)
        return prompt
    except Exception as e:
        logger.error(f"Error getting dynamic prompt for {agent_name}: {e}")
        raise

async def load_dynamic_tools_for_agent(
    tenant_id: str, agent_name: str, base_tools: list
) -> list:
    """Load dynamic tools for a specific agent from S3 configuration."""
    if not tenant_id:
        return base_tools

    try:
        from utils.dynamic_agent_loader import (
            load_dynamic_agents_config,
            create_dynamic_tools,
            filter_tools_by_names,
        )

        # Cargar configuración de herramientas dinámicas
        tools_config = await load_dynamic_agents_config(tenant_id, "tools")
        if not tools_config:
            return base_tools

        # Buscar configuración específica para este agente
        agent_tools_config = tools_config.get(agent_name, {})
        if not agent_tools_config:
            return base_tools

        # Crear herramientas dinámicas
        dynamic_tools = await create_dynamic_tools(
            tenant_id, agent_tools_config, base_tools
        )

        # Filtrar herramientas si se especifica
        if "tool_names" in agent_tools_config:
            filtered_tools = filter_tools_by_names(
                base_tools + dynamic_tools, agent_tools_config["tool_names"]
            )
            return filtered_tools

        return base_tools + dynamic_tools

    except Exception as e:
        logger.warning(
            f"No se pudieron cargar herramientas dinámicas para {agent_name}: {e}"
        )
        return base_tools

async def create_dynamic_agents_from_config(
    tenant_id: str, available_llms: dict, available_tools: list
) -> dict:
    """
    Crea agentes dinámicamente desde la configuración en S3.

    Args:
        tenant_id: ID del tenant
        available_llms: Diccionario de LLMs disponibles
        available_tools: Lista de herramientas disponibles

    Returns:
        Diccionario con los agentes creados
    """
    try:
        from utils.dynamic_agent_loader import (
            load_dynamic_agents_config,
            create_dynamic_agent,
        )

        # Cargar configuración de agentes dinámicos
        agents_config = await load_dynamic_agents_config(tenant_id, "agents")
        if not agents_config:
            logger.error(
                f"No se encontró configuración de agentes dinámicos para tenant {tenant_id}. El sistema requiere configuración dinámica."
            )
            raise Exception(
                f"No se encontró configuración de agentes dinámicos para tenant {tenant_id}"
            )

        dynamic_agents = {}

        for agent_name, agent_config in agents_config.items():
            try:
                # Crear agente dinámicamente
                agent = await create_dynamic_agent(
                    tenant_id=tenant_id,
                    agent_name=agent_name,
                    agent_config=agent_config,
                    available_tools=available_tools,
                    available_llms=available_llms,
                )

                if agent:
                    dynamic_agents[agent_name] = agent
                    logger.info(f"Agente dinámico '{agent_name}' creado exitosamente")
                else:
                    logger.error(f"No se pudo crear el agente dinámico '{agent_name}'")

            except Exception as e:
                logger.error(f"Error creando agente dinámico '{agent_name}': {e}")
                continue

        if not dynamic_agents:
            raise Exception(
                f"No se pudo crear ningún agente dinámico para tenant {tenant_id}"
            )

        return dynamic_agents

    except Exception as e:
        logger.error(f"Error cargando agentes dinámicos para tenant {tenant_id}: {e}")
        raise


async def get_all_available_tools() -> list:
    """
    Obtiene todas las herramientas disponibles en el sistema.

    Returns:
        Lista de todas las herramientas disponibles
    """
    tools = []

    try:
        # Importar todas las herramientas de los diferentes módulos
        from tools.system.system import get_datetime, invalidate_cache
        from tools.actividades.actividades_tool import (
            list_actividades, create_actividad, update_actividad, delete_actividad,
            consultar_disponibilidad,
        )
        from tools.asociados.asociados_tool import list_asociados, buscar_asociados
        # Agregar todas las herramientas
        tools.extend(
            [
                get_datetime,
                invalidate_cache,
                list_actividades,
                create_actividad,
                update_actividad,
                delete_actividad,
                consultar_disponibilidad,
                list_asociados,
                buscar_asociados,
            ]
        )

    except Exception as e:
        logger.error(f"Error obteniendo herramientas disponibles: {e}")

    return tools


async def create_dynamic_supervisors_from_config(
    tenant_id: str, available_llms: dict, available_agents: list
) -> dict:
    """
    Crea supervisores dinámicamente desde la configuración en S3.

    Args:
        tenant_id: ID del tenant
        available_llms: Diccionario de LLMs disponibles
        available_agents: Lista de agentes disponibles

    Returns:
        Diccionario con los supervisores creados
    """
    try:
        from utils.dynamic_agent_loader import (
            load_dynamic_agents_config,
            create_dynamic_supervisor,
        )

        # Cargar configuración de supervisores dinámicos
        supervisors_config = await load_dynamic_agents_config(tenant_id, "supervisor")
        if not supervisors_config:
            logger.error(
                f"No se encontró configuración de supervisores dinámicos para tenant {tenant_id}. El sistema requiere configuración dinámica."
            )
            raise Exception(
                f"No se encontró configuración de supervisores dinámicos para tenant {tenant_id}"
            )

        dynamic_supervisors = {}

        for supervisor_name, supervisor_config in supervisors_config.items():
            try:
                # Crear supervisor dinámicamente
                supervisor = await create_dynamic_supervisor(
                    tenant_id=tenant_id,
                    supervisor_name=supervisor_name,
                    supervisor_config=supervisor_config,
                    available_agents=available_agents,
                    available_llms=available_llms,
                )

                if supervisor:
                    dynamic_supervisors[supervisor_name] = supervisor
                    logger.info(
                        f"Supervisor dinámico '{supervisor_name}' creado exitosamente"
                    )
                else:
                    logger.error(
                        f"No se pudo crear el supervisor dinámico '{supervisor_name}'"
                    )

            except Exception as e:
                logger.error(
                    f"Error creando supervisor dinámico '{supervisor_name}': {e}"
                )
                continue

        if not dynamic_supervisors:
            raise Exception(
                f"No se pudo crear ningún supervisor dinámico para tenant {tenant_id}"
            )

        return dynamic_supervisors

    except Exception as e:
        logger.error(
            f"Error cargando supervisores dinámicos para tenant {tenant_id}: {e}"
        )
        raise
