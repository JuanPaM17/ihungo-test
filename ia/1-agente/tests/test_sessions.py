"""
Tests de aislamiento de sesiones — caso J.

J1 — dos sesiones distintas no comparten memoria del grafo.
     Se verifica usando InMemorySaver con thread_id distintos.

NOTA: Este test verifica el mecanismo de checkpointing de LangGraph
(thread_id distinto → estado distinto). No ejecuta el grafo completo
con LLM real. Verifica directamente que aget_state devuelve None
para un thread_id nuevo.
"""

import pytest
from unittest.mock import patch, AsyncMock
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage


class SimpleState(TypedDict):
    messages: Annotated[list, add_messages]


async def _build_minimal_graph():
    """Grafo mínimo con InMemorySaver para probar aislamiento de sesiones."""
    async def echo_node(state):
        return {"messages": [AIMessage(content="echo")]}

    workflow = StateGraph(SimpleState)
    workflow.add_node("echo", echo_node)
    workflow.add_edge(START, "echo")
    workflow.add_edge("echo", END)
    checkpointer = InMemorySaver()
    return workflow.compile(checkpointer=checkpointer)


class TestSessionIsolation:

    async def test_different_threads_have_different_state(self):
        """
        J1 — thread_id A y thread_id B tienen estados independientes.
        Después de invocar con A, el estado de B sigue vacío.
        """
        graph = await _build_minimal_graph()

        config_a = RunnableConfig(configurable={"thread_id": "session-A"})
        config_b = RunnableConfig(configurable={"thread_id": "session-B"})

        # Invocar solo con sesión A
        await graph.ainvoke(
            {"messages": [HumanMessage(content="Hola desde A")]},
            config_a,
        )

        # Estado de A tiene mensajes
        state_a = await graph.aget_state(config_a)
        assert len(state_a.values.get("messages", [])) > 0

        # Estado de B sigue vacío — no comparte memoria con A
        state_b = await graph.aget_state(config_b)
        assert len(state_b.values.get("messages", [])) == 0

    async def test_same_thread_accumulates_state(self):
        """
        J2 — la misma sesión acumula mensajes entre invocaciones.
        """
        graph = await _build_minimal_graph()
        config = RunnableConfig(configurable={"thread_id": "session-persist"})

        await graph.ainvoke(
            {"messages": [HumanMessage(content="Mensaje 1")]}, config
        )
        await graph.ainvoke(
            {"messages": [HumanMessage(content="Mensaje 2")]}, config
        )

        state = await graph.aget_state(config)
        messages = state.values.get("messages", [])
        # Debe tener al menos los 2 HumanMessages + respuestas del nodo
        human_msgs = [m for m in messages if isinstance(m, HumanMessage)]
        assert len(human_msgs) >= 2
