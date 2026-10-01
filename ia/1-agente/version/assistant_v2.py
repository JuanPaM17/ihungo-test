import os
import json
import time
import traceback
from typing import Optional, Dict, Any, AsyncIterator
from rich.console import Console
from langgraph.types import StateSnapshot
from langchain_core.runnables import RunnableConfig
from utils.langgraph_utils import format_prompt
from graphs.assistant_state import EvaluatorState
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    ToolMessage,
    AIMessage,
)
import logging
from dotenv import load_dotenv
from graphs.utils import innermost_subgraph_state
from graphs.supervisor_evaluator_summarizer import (
    instantiate_supervisor,
    instantiate_supervisor_anonymous,
    instantiate_supervisor_by_role,
)
from langchain_core.tracers.context import tracing_v2_enabled
from utils.observability import write_turn_log

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console = Console()

load_dotenv()

class AssistantV2:

    """
    Assistant V2 implementation with enhanced capabilities and improved architecture.
    Integrates with the supervisor-evaluator-summarizer architecture for better
    task delegation, evaluation, and response quality.
    """

    def __init__(self, tenant_id: str, version: str = "v2"):
        self.tenant_id = tenant_id
        self.version = version
        self.available_llms = {}

    async def initialize(self):
        """Initialize the assistant with all required components."""
        await self._initialize_llms()

    async def _initialize_llms(self):
        """Initialize the available language models via LLMProvider abstraction."""
        from utils.llm_provider import build_available_llms
        self.available_llms = build_available_llms()

    async def build_main_graph(self, state: Dict[str, Any] = {}):
        """Build the main processing graph using the supervisor-evaluator-summarizer architecture."""
        try:
            role = state.get("role", "associate")
            from graphs.supervisor_evaluator_summarizer import create_graph

            if role == "admin":
                supervisor, recursion_limit = await instantiate_supervisor(
                    self.available_llms, self.tenant_id, state
                )
                supervisor_node = "supervisor"
            else:
                supervisor, recursion_limit = await instantiate_supervisor_by_role(
                    self.available_llms, self.tenant_id, state, role
                )
                supervisor_node = f"supervisor_{role}"

            main_graph = await create_graph(
                self.available_llms, self.tenant_id, state, supervisor, supervisor_node, recursion_limit
            )
            if main_graph is None:
                raise RuntimeError(
                    "create_graph returned None for tenant "
                    f"{self.tenant_id}"
                )
            return main_graph, recursion_limit
        except Exception as e:
            logger.exception("Error building supervisor graph")
            raise

class AssistantV2Manager:
    """Manager class for handling multiple Assistant V2 instances."""

    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.assistants: Dict[str, AssistantV2] = {}

    async def get_graph_for_tenant(
        self,
        tenant_id: str,
        version: str = "v2",
        state: Dict[str, Any] = {},
    ):
        """Get or create a graph for a specific tenant based on role.

        Returns:
            (graph, recursion_limit)
        """
        role = state.get("role", "associate")
        cache_key = f"{tenant_id}_{role}"

        if cache_key not in self.cache:
            assistant = AssistantV2(tenant_id, version)
            await assistant.initialize()
            self.assistants[cache_key] = assistant
            self.cache[cache_key] = await assistant.build_main_graph(state)

        graph, recursion_limit = self.cache[cache_key]
        if graph is None:
            raise RuntimeError(
                f"Assistant graph could not be built for tenant={tenant_id} version={version}"
            )
        return graph, recursion_limit

    def get_assistant_for_tenant(self, tenant_id: str, state: Dict[str, Any] = {}):
        """Get the assistant instance for a specific tenant."""
        role = state.get("role", "associate")
        cache_key = f"{tenant_id}_{role}"
        return self.assistants.get(cache_key)

assistant_manager = AssistantV2Manager()

async def process_query_v2(
    tenant_id: str,
    query: str,
    thread_id: str,
    token: str,
    document: str = "_None_",
    user_name: str = "_None_",
    is_anonymous: bool = True,
    role: str = "associate",
    language: str = "en",
    version: str = "v2",
) -> str:

    user_state = {
        "user_name": user_name,
        "is_anonymous": is_anonymous,
        "role": role,
        "document": document,
        "language": language.upper(),
    }

    # Get the main graph
    main_graph, recursion_limit = await assistant_manager.get_graph_for_tenant(
        tenant_id, version, user_state
    )
    if main_graph is None:
        raise RuntimeError(
            f"Assistant graph is not available for tenant={tenant_id} version={version}"
        )

    configuration = RunnableConfig(
        recursion_limit=recursion_limit,
        tags=["conversation"],
        metadata={
            "session_id": thread_id,
            "tenant_id": tenant_id,
            "namespace": tenant_id,
        },
        configurable={
            "tenant_id": tenant_id,
            "namespace": tenant_id,
            "thread_id": thread_id,
            "version": version,
            "token": token,
        },
    )

    existing_state = None
    try:
        state_snapshot: StateSnapshot = await main_graph.aget_state(
            configuration, subgraphs=True
        )
        existing_state = innermost_subgraph_state(state_snapshot)
    except Exception as e:
        logger.info("Error getting current state: %s", str(e))

    existing_state_history = []
    if existing_state is not None:
        existing_state_history = existing_state.values.get("messages", [])

    # Index where turn messages start (for metrics extraction)
    turn_start_index = len(existing_state_history)

    t0 = time.monotonic()
    obs_error: Optional[str] = None
    try:
        with tracing_v2_enabled(project_name=tenant_id):
            if not existing_state_history:
                # Initialize new state with user context
                logger.info("Initializing new state for thread: %s", thread_id)

                from utils.tenant_config import get_agent_prompt

                dynamic_prompt = await get_agent_prompt(
                    tenant_id, "general_prompt.md", prompt_type="system"
                )

                system_prompt = format_prompt(user_state, str(dynamic_prompt))

                initial_messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=query),
                ]

                initial_state = EvaluatorState(
                    messages=initial_messages,
                    document=document,
                    is_anonymous=is_anonymous,
                    token=token,
                    user_name=user_name,
                    language=language.upper(),
                    trial=0,
                )

                await main_graph.ainvoke(initial_state, configuration)
            else:
                # Update existing state with new user input
                logger.info("Updating existing state for thread: %s", thread_id)
                updated_messages = existing_state.values.get("messages", [])
                updated_messages.append(HumanMessage(content=query))

                from utils.tenant_config import get_agent_prompt

                dynamic_prompt = await get_agent_prompt(
                    tenant_id, "general_prompt.md", prompt_type="system"
                )

                system_prompt = format_prompt(user_state, str(dynamic_prompt))

                updated_messages = [
                    msg for msg in updated_messages if not isinstance(msg, SystemMessage)
                ]
                updated_messages.insert(0, SystemMessage(content=system_prompt))

                updated_state = EvaluatorState(
                    messages=updated_messages,
                    document=document,
                    is_anonymous=is_anonymous,
                    token=token,
                    user_name=user_name,
                    language=language.upper(),
                    trial=0,
                )

                await main_graph.ainvoke(updated_state, configuration)

    except Exception as exc:
        latency_ms = int((time.monotonic() - t0) * 1000)
        obs_error = type(exc).__name__
        await write_turn_log(
            session_id=thread_id,
            latency_ms=latency_ms,
            status="error",
            error=obs_error,
        )
        raise

    # Get the final state after processing
    final_state_snapshot: StateSnapshot = await main_graph.aget_state(
        configuration, subgraphs=True
    )
    final_state = innermost_subgraph_state(final_state_snapshot)
    messages = final_state.values.get("messages", [])
    response = messages[-1].content if messages else ""

    latency_ms = int((time.monotonic() - t0) * 1000)
    await write_turn_log(
        session_id=thread_id,
        latency_ms=latency_ms,
        status="success",
        messages=messages,
        turn_start_index=turn_start_index,
    )

    return response


# ── SSE nodes that produce user-visible tokens ────────────────────────────────
_SUMMARIZER_NODE = "summarizer"
# Nodes whose token stream is internal reasoning — never sent to the client
_INTERNAL_NODES = {"evaluator"}


def _sse(event: str, data: dict) -> str:
    """Format a single SSE frame."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_query_v2(
    tenant_id: str,
    query: str,
    thread_id: str,
    token: str,
    session_id: str,
    document: str = "_None_",
    user_name: str = "_None_",
    is_anonymous: bool = True,
    role: str = "associate",
    language: str = "en",
    version: str = "v2",
) -> AsyncIterator[str]:
    """
    Async generator that yields SSE-formatted strings while the V2 graph runs.

    Events emitted:
      start       — graph begins, includes session_id
      routing     — supervisor or agent node activated
      tool_start  — a tool is about to be called
      tool_end    — a tool finished
      token       — a text chunk from the summarizer (final response)
      done        — graph finished, includes full response
      error       — unrecoverable error with safe message
    """
    user_state = {
        "user_name": user_name,
        "is_anonymous": is_anonymous,
        "role": role,
        "document": document,
        "language": language.upper(),
    }

    try:
        main_graph, recursion_limit = await assistant_manager.get_graph_for_tenant(
            tenant_id, version, user_state
        )
    except Exception:
        logger.exception("stream_query_v2: failed to build graph")
        yield _sse("error", {"type": "internal_error", "message": "No se pudo iniciar el asistente."})
        return

    configuration = RunnableConfig(
        recursion_limit=recursion_limit,
        tags=["conversation"],
        metadata={"session_id": thread_id, "tenant_id": tenant_id, "namespace": tenant_id},
        configurable={
            "tenant_id": tenant_id,
            "namespace": tenant_id,
            "thread_id": thread_id,
            "version": version,
            "token": token,
        },
    )

    # Build initial state (same logic as process_query_v2)
    existing_state = None
    try:
        snap: StateSnapshot = await main_graph.aget_state(configuration, subgraphs=True)
        existing_state = innermost_subgraph_state(snap)
    except Exception:
        pass

    existing_messages = []
    if existing_state is not None:
        existing_messages = existing_state.values.get("messages", [])

    turn_start_index = len(existing_messages)

    from utils.tenant_config import get_agent_prompt

    dynamic_prompt = await get_agent_prompt(tenant_id, "general_prompt.md", prompt_type="system")
    system_prompt = format_prompt(user_state, str(dynamic_prompt))

    if not existing_messages:
        initial_messages = [SystemMessage(content=system_prompt), HumanMessage(content=query)]
        input_state = EvaluatorState(
            messages=initial_messages,
            document=document,
            is_anonymous=is_anonymous,
            token=token,
            user_name=user_name,
            language=language.upper(),
            trial=0,
        )
    else:
        updated = [msg for msg in existing_messages if not isinstance(msg, SystemMessage)]
        updated.insert(0, SystemMessage(content=system_prompt))
        updated.append(HumanMessage(content=query))
        input_state = EvaluatorState(
            messages=updated,
            document=document,
            is_anonymous=is_anonymous,
            token=token,
            user_name=user_name,
            language=language.upper(),
            trial=0,
        )

    yield _sse("start", {"session_id": session_id})

    final_response_parts: list[str] = []
    seen_nodes: set[str] = set()
    t0 = time.monotonic()

    try:
        with tracing_v2_enabled(project_name=tenant_id):
            async for event in main_graph.astream_events(
                input_state, configuration, version="v2"
            ):
                kind: str = event.get("event", "")
                name: str = event.get("name", "")
                metadata: dict = event.get("metadata", {})
                node: str = metadata.get("langgraph_node", "")
                data: dict = event.get("data", {})

                # ── routing ──────────────────────────────────────────────────
                if kind == "on_chain_start" and node and node not in seen_nodes:
                    if node not in (_SUMMARIZER_NODE, "evaluator", "__start__", "tools"):
                        seen_nodes.add(node)
                        yield _sse("routing", {"node": node})

                # ── tool_start ───────────────────────────────────────────────
                elif kind == "on_tool_start":
                    tool_name = name or data.get("input", {})
                    yield _sse("tool_start", {"tool": tool_name})

                # ── tool_end ─────────────────────────────────────────────────
                elif kind == "on_tool_end":
                    tool_name = name
                    output = data.get("output")
                    if isinstance(output, dict) and "error" in output:
                        status = "error"
                    else:
                        status = "success"
                    yield _sse("tool_end", {"tool": tool_name, "status": status})

                # ── token (summarizer only) ───────────────────────────────────
                elif kind == "on_chat_model_stream" and node == _SUMMARIZER_NODE:
                    chunk = data.get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        final_response_parts.append(chunk.content)
                        yield _sse("token", {"content": chunk.content})

    except Exception as e:
        latency_ms = int((time.monotonic() - t0) * 1000)
        logger.error("stream_query_v2: error during streaming: %s", e)
        await write_turn_log(
            session_id=session_id,
            latency_ms=latency_ms,
            status="error",
            error=type(e).__name__,
        )
        yield _sse("error", {"type": "stream_error", "message": "Ocurrió un error procesando la solicitud."})
        return

    # Final response from accumulated tokens or fallback to state
    final_response = "".join(final_response_parts)
    final_messages: list = []
    if not final_response:
        try:
            snap = await main_graph.aget_state(configuration, subgraphs=True)
            fs = innermost_subgraph_state(snap)
            final_messages = fs.values.get("messages", [])
            final_response = final_messages[-1].content if final_messages else ""
        except Exception:
            final_response = ""
    else:
        try:
            snap = await main_graph.aget_state(configuration, subgraphs=True)
            fs = innermost_subgraph_state(snap)
            final_messages = fs.values.get("messages", [])
        except Exception:
            pass

    latency_ms = int((time.monotonic() - t0) * 1000)
    await write_turn_log(
        session_id=session_id,
        latency_ms=latency_ms,
        status="success",
        messages=final_messages,
        turn_start_index=turn_start_index,
    )

    yield _sse("done", {"response": final_response, "session_id": session_id})
