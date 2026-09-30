# version/assistant_v1.py
import json
import importlib
from pathlib import Path
import time
import logging
from typing import Dict

from pydantic import create_model, Field
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool

from utils import init_llm, get_llm
from langchain_core.tracers.context import tracing_v2_enabled

logger = logging.getLogger(__name__)

# Ruta al JSON de configuración
BASE_DIR    = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config" / "v1" / "tools_config.json"

def load_tools_from_json(path: str):
    """Carga la descripción y las tools desde el JSON."""
    with open(path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    tools = []
    for name, conf in cfg["tools"].items():
        mod       = importlib.import_module(conf["module"])
        ToolClass = getattr(mod, conf["class"])

        params = {}
        for arg, info in conf.get("fields", {}).items():
            py_type = eval(info["type"])
            params[arg] = (py_type, Field(..., description=info["description"]))
        ArgsModel = create_model(f"{name.title()}Params", **params)

        # Soporta tanto clases con get_tool() como objetos @tool directos
        if isinstance(ToolClass, StructuredTool):
            original_tool = ToolClass
        else:
            original_tool = ToolClass.get_tool()

        tool = StructuredTool.from_function(
            name        = name,
            description = conf["description"],
            coroutine   = original_tool.coroutine,
            args_schema = ArgsModel,
        )
        tools.append(tool)

    return cfg["agent"]["description"], tools

AGENT_DESCRIPTION, BASE_TOOLS = load_tools_from_json(str(CONFIG_PATH))

# Cache solo para instancias de LLM por tenant-version
_LLM_CACHE: Dict[str, any] = {}

def build_graph(llm_with_tools, tools_list):
    """Crea el StateGraph usando la lista de tools que le pases."""
    def assistant_node(state: MessagesState):
        system = HumanMessage(content=AGENT_DESCRIPTION)
        resp   = llm_with_tools.invoke([system] + state["messages"])
        return {"messages": [resp]}

    builder = StateGraph(MessagesState)
    builder.add_node("assistant", assistant_node)
    builder.add_node("tools", ToolNode(tools_list))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")
    return builder.compile(checkpointer=MemorySaver())

def extract_output(result: dict) -> str:
    """Extrae el contenido del último mensaje con .content"""
    for msg in reversed(result.get("messages", [])):
        if hasattr(msg, "content"):
            return msg.content
    return "No se obtuvo respuesta del modelo."

async def process_query_v1(
    tenant_id: str,
    query: str,
    thread_id: str,
    token: str,
    document: dict,
    user_name: str,
    language: str,
    version: str,
    is_anonymous: bool,
) -> str:
    start = time.time()
    key   = f"{tenant_id}-{version}"

    if key not in _LLM_CACHE:
        _LLM_CACHE[key] = get_llm(tenant_id, version) or init_llm(tenant_id, version)
    llm = _LLM_CACHE[key]

    tokenized_tools = []
    for original in BASE_TOOLS:
        def make_wrapper(coro, jwt, tid):
            async def wrapper(**kwargs):
                return await coro(**{**kwargs, "token": jwt, "tenant_id": tid})
            return wrapper

        wrapper = make_wrapper(original.coroutine, token, tenant_id)
        tokenized_tools.append(
            StructuredTool.from_function(
                name        = original.name,
                description = original.description,
                coroutine   = wrapper,
                args_schema = original.args_schema,
            )
        )

    llm_with_tools = llm.bind_tools(tokenized_tools)
    graph = build_graph(llm_with_tools, tokenized_tools)


    messages = [
        SystemMessage(
            content=(
                "🔐 Tu JWT de autorización es:\n"
                f"{token}\n\n"
            )
        ),
        HumanMessage(content=query),
    ]

    with tracing_v2_enabled(project_name=tenant_id):
        result = await graph.ainvoke(
            {"messages": messages},
            {"configurable": {"thread_id": thread_id}}
        )

    output = extract_output(result)
    logger.info("Tiempo process_query_v1=%.3f s", time.time() - start)
    return output
