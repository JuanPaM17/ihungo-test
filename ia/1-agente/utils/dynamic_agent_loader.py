import logging
import json
import os
import copy
from typing import Dict, List, Any, Optional
from utils.tenant_config import get_agent_prompt

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def load_dynamic_agents_config(tenant_id: str, config_type: str = "agents") -> Dict[str, Dict]:
    """
    Carga la configuracion de agentes dinamicos desde S3.
    
    Args:
        tenant_id: ID del tenant
        config_type: Tipo de configuracion ("agents", "supervisor")
        
    Returns:
        Dict con la configuracion de agentes
    """
    try:
        # Cargar configuracion tenant-specific desde el root del tenant.
        # Este archivo no se hereda desde config/v2 global.
        from utils.tenant_config import get_json_from_local

        config_data = get_json_from_local(tenant_id, "dynamic_agents_config.json")

        # Extraer la seccion correspondiente
        if config_type == "agents":
            return config_data.get("dynamic_agents", {})
        if config_type == "supervisor":
            return config_data.get("supervisor_config", {})

        return config_data

    except Exception as e:
        logger.error(f"Error cargando configuracion dinamica para tenant {tenant_id}: {e}")
        return {}

async def create_dynamic_agent(
    tenant_id: str,
    agent_name: str,
    agent_config: Dict[str, Any],
    available_tools: List,
    available_llms: Dict
) -> Optional[Any]:
    """
    Crea un agente dinámicamente basado en la configuración.
    
    Args:
        tenant_id: ID del tenant
        agent_name: Nombre del agente
        agent_config: Configuración del agente
        available_tools: Lista de herramientas disponibles
        available_llms: Diccionario de LLMs disponibles
        
    Returns:
        Instancia del agente creado o None si falla
    """
    try:
        # Validar configuración requerida
        required_fields = ["prompt_path"]
        for field in required_fields:
            if field not in agent_config:
                logger.error(f"Agente '{agent_name}' falta campo requerido: {field}")
                return None
        
        # Cargar prompt dinámicamente
        prompt = await get_agent_prompt(tenant_id, agent_config["prompt_path"], "agent")
        if not prompt:
            logger.error(f"Agente '{agent_name}' no pudo cargar prompt desde {agent_config['prompt_path']}")
            return None
        
        # Obtener herramientas específicas del agente
        agent_tools = []
        if "tool_names" in agent_config:
            tool_names = agent_config["tool_names"]
            if isinstance(tool_names, list):
                agent_tools = [tool for tool in available_tools if tool.name in tool_names]
            elif isinstance(tool_names, str):
                agent_tools = [tool for tool in available_tools if tool.name == tool_names]
        
        # Si no se especificaron herramientas, usar lista vacía (para agentes como greeting)
        if not agent_tools and "tool_names" not in agent_config:
            agent_tools = []
        
        # Obtener LLM para el agente
        llm_model = agent_config.get("llm_model", "gpt-4.1-mini")
        llm = available_llms.get(llm_model)
        if not llm:
            logger.error(f"LLM '{llm_model}' no disponible para agente '{agent_name}'")
            return None
        
        agent_type = str(agent_config.get("agent_type", "react")).lower()
        if agent_type != "react":
            logger.warning(
                "Agente '%s' usa agent_type='%s' no soportado; se aplicara create_react_agent por compatibilidad.",
                agent_name,
                agent_type,
            )

        from langgraph.prebuilt import create_react_agent
        agent = create_react_agent(
            model=llm,
            tools=agent_tools,
            name=agent_name,
            prompt=prompt,
            debug=False
        )
        
        logger.info(f"Agente dinámico '{agent_name}' creado exitosamente")
        return agent
        
    except Exception as e:
        logger.error(f"Error creando agente dinámico '{agent_name}': {e}")
        return None


async def create_dynamic_tools(
    tenant_id: str,
    tools_config: Dict[str, Dict],
    available_tools: List
) -> List:
    """
    Crea herramientas dinámicamente basadas en la configuración.
    
    Args:
        tenant_id: ID del tenant
        tools_config: Configuración de herramientas
        available_tools: Lista de herramientas base disponibles
        
    Returns:
        Lista de herramientas dinámicas creadas
    """
    dynamic_tools = []
    
    for tool_name, tool_config in tools_config.items():
        try:
            # Buscar la herramienta base
            base_tool = None
            for tool in available_tools:
                if tool.name == tool_config.get("base_tool_name", tool_name):
                    base_tool = copy.deepcopy(tool)
                    break
            
            if not base_tool:
                logger.warning(f"Herramienta base '{tool_config.get('base_tool_name', tool_name)}' no encontrada")
                continue
            
            # Aplicar configuración dinámica si existe
            if "description" in tool_config:
                base_tool.description = tool_config["description"]
            
            if "name" in tool_config:
                base_tool.name = tool_config["name"]
            
            dynamic_tools.append(base_tool)
            logger.info(f"Herramienta dinámica '{tool_name}' creada exitosamente")
            
        except Exception as e:
            logger.error(f"Error creando herramienta dinámica '{tool_name}': {e}")
    
    return dynamic_tools


def filter_tools_by_names(tools: List, tool_names: List[str]) -> List:
    """
    Filtra herramientas por nombres.
    
    Args:
        tools: Lista de herramientas disponibles
        tool_names: Lista de nombres de herramientas a incluir
        
    Returns:
        Lista filtrada de herramientas
    """
    if not tool_names:
        return tools
    
    filtered_tools = []
    for tool in tools:
        if tool.name in tool_names:
            filtered_tools.append(tool)
    
    return filtered_tools


async def create_dynamic_supervisor(
    tenant_id: str,
    supervisor_name: str,
    supervisor_config: Dict[str, Any],
    available_agents: List,
    available_llms: Dict
) -> Optional[Any]:
    """
    Crea un supervisor dinámicamente basado en la configuración.
    
    Args:
        tenant_id: ID del tenant
        supervisor_name: Nombre del supervisor
        supervisor_config: Configuración del supervisor
        available_agents: Lista de agentes disponibles
        available_llms: Diccionario de LLMs disponibles
        
    Returns:
        Instancia del supervisor creado o None si falla
    """
    try:
        # Validar configuración requerida
        required_fields = ["prompt_path"]
        for field in required_fields:
            if field not in supervisor_config:
                logger.error(f"Supervisor '{supervisor_name}' falta campo requerido: {field}")
                return None
        
        # Cargar prompt dinámicamente
        prompt = await get_agent_prompt(tenant_id, supervisor_config["prompt_path"], "supervisor")
        if not prompt:
            logger.error(f"Supervisor '{supervisor_name}' no pudo cargar prompt desde {supervisor_config['prompt_path']}")
            return None
        
        # Obtener LLM para el supervisor
        llm_model = supervisor_config.get("llm_model", "gpt-4.1-mini")
        llm = available_llms.get(llm_model)
        if not llm:
            logger.error(f"LLM '{llm_model}' no disponible para supervisor '{supervisor_name}'")
            return None
        
        # Filtrar agentes basado en la configuración
        supervisor_agents = available_agents
        if "agent_names" in supervisor_config:
            agent_names = supervisor_config["agent_names"]
            if isinstance(agent_names, list):
                # Crear un diccionario de agentes por nombre para facilitar el filtrado
                agents_dict = {agent.name: agent for agent in available_agents}
                filtered_agents = []
                missing_agents = []
                
                for agent_name in agent_names:
                    if agent_name in agents_dict:
                        filtered_agents.append(agents_dict[agent_name])
                    else:
                        missing_agents.append(agent_name)
                
                if missing_agents:
                    logger.warning(f"Supervisor '{supervisor_name}' - agentes no encontrados: {missing_agents}")
                
                supervisor_agents = filtered_agents
                logger.info(f"Supervisor '{supervisor_name}' - agentes filtrados: {[agent.name for agent in supervisor_agents]}")
            else:
                logger.warning(f"Supervisor '{supervisor_name}' - agent_names debe ser una lista, usando todos los agentes disponibles")
        else:
            logger.info(f"Supervisor '{supervisor_name}' - no se especificaron agent_names, usando todos los agentes disponibles")
        
        # Crear handoff tools para los agentes filtrados
        from langgraph_supervisor import create_handoff_tool
        handoff_tools = []
        handoff_descriptions = supervisor_config.get("handoff_descriptions", {})

        for agent in supervisor_agents:
            description = handoff_descriptions.get(
                agent.name,
                f"Use '{agent.name}' to handle related tasks."
            )
            handoff_tool = create_handoff_tool(
                agent_name=agent.name,
                name=f"transfer_to_{agent.name}",
                description=description,
            )
            logger.info(f"Handoff tool '{agent.name}': {description}")
            handoff_tools.append(handoff_tool)
        
        # Crear supervisor con los agentes filtrados
        from langgraph_supervisor import create_supervisor
        supervisor = create_supervisor(
            supervisor_agents,
            tools=handoff_tools,
            model=available_llms.get(llm_model),
            output_mode="full_history",  # "last_message", "full_history",
            add_handoff_messages=False,  # Add handoff tool invocations to the history
            prompt=prompt,
        )
        
        recursion_limit = supervisor_config.get("recursion_limit", 25)
        logger.info(f"Supervisor dinámico '{supervisor_name}' creado exitosamente con {len(supervisor_agents)} agentes (recursion_limit={recursion_limit})")
        return {"graph": supervisor, "recursion_limit": recursion_limit}

    except Exception as e:
        logger.error(f"Error creando supervisor dinámico '{supervisor_name}': {e}")
        return None
