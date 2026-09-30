import os
import traceback
from typing import Optional, Dict, Any, List
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
)
from langchain_core.tracers.context import tracing_v2_enabled

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
        """Initialize the available language models for the supervisor architecture."""
        from langchain.chat_models import init_chat_model

        # Initialize different LLMs for different purposes
        self.available_llms = {
            "gpt-4.1-nano": init_chat_model(
                model="gpt-4.1-nano",
                temperature=os.getenv("LLM_TEMPERATURE", 0.0),
                api_key=os.getenv("OPENAI_API_KEY"),
            ),
            "gpt-4o-mini": init_chat_model(
                model="gpt-4o-mini",
                temperature=os.getenv("LLM_TEMPERATURE", 0.0),
                api_key=os.getenv("OPENAI_API_KEY"),
            ),
            "gpt-4.1-mini": init_chat_model(
                model="gpt-4.1-mini",
                temperature=os.getenv("LLM_TEMPERATURE", 0.0),
                api_key=os.getenv("OPENAI_API_KEY"),
            ),
        }

    async def build_main_graph(self, state: Dict[str, Any] = {}):
        """Build the main processing graph using the supervisor-evaluator-summarizer architecture."""
        try:
            # Determine graph type from state
            is_anonymous = state.get("is_anonymous", False)
            from graphs.supervisor_evaluator_summarizer import create_graph

            # Use the supervisor graph architecture based on is_anonymous
            if is_anonymous:
                # Create anonymous supervisor graph
                supervisor = await instantiate_supervisor_anonymous(
                    self.available_llms, self.tenant_id, state
                )
            else:
                # Create supervisor graph
                supervisor = await instantiate_supervisor(
                    self.available_llms, self.tenant_id, state
                )

            main_graph = await create_graph(
                self.available_llms, self.tenant_id, state, supervisor
            )
            if main_graph is None:
                raise RuntimeError(
                    "create_graph returned None for tenant "
                    f"{self.tenant_id} (is_anonymous={is_anonymous})"
                )
            return main_graph
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
        """Get or create a graph for a specific tenant based on is_anonymous."""
        is_anonymous = state.get("is_anonymous", False)
        cache_key = f"{tenant_id}_{'anonymous' if is_anonymous else ''}"

        if cache_key not in self.cache:
            assistant = AssistantV2(tenant_id, version)
            await assistant.initialize()
            self.assistants[cache_key] = assistant
            self.cache[cache_key] = await assistant.build_main_graph(state)
        graph = self.cache[cache_key]
        if graph is None:
            raise RuntimeError(
                f"Assistant graph could not be built for tenant={tenant_id} "
                f"version={version} is_anonymous={is_anonymous}"
            )
        return graph

    def get_assistant_for_tenant(self, tenant_id: str, state: Dict[str, Any] = {}):
        """Get the assistant instance for a specific tenant."""
        is_anonymous = state.get("is_anonymous", False)
        cache_key = f"{tenant_id}_{'anonymous' if is_anonymous else ''}"
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
    language: str = "en",
    version: str = "v2",
    
) -> str:

    user_state = {
        "user_name": user_name,
        "is_anonymous": is_anonymous,
        "document": document,
        "language": language.upper(),
    }

    # Get the main graph
    main_graph = await assistant_manager.get_graph_for_tenant(
        tenant_id, version, user_state
    )
    if main_graph is None:
        raise RuntimeError(
            f"Assistant graph is not available for tenant={tenant_id} version={version}"
        )

    configuration = RunnableConfig(
        tags=["conversation"],
        metadata={
            "session_id": token,
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

    with tracing_v2_enabled(project_name=tenant_id):
        if not existing_state_history:
            # Initialize new state with user context
            logger.info("Initializing new state for thread: %s", thread_id)

            # Create prompt template with user context
            from utils.tenant_config import get_agent_prompt

            dynamic_prompt = await get_agent_prompt(
                tenant_id, "general_prompt.md", prompt_type="system"
            )

            system_prompt = format_prompt(user_state, str(dynamic_prompt))

            # Prepare initial messages with SystemMessage at the beginning
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
            # Create new state with updated messages
            updated_messages = existing_state.values.get("messages", [])
            updated_messages.append(HumanMessage(content=query))

            # Create prompt template with user context
            from utils.tenant_config import get_agent_prompt

            dynamic_prompt = await get_agent_prompt(
                tenant_id, "general_prompt.md", prompt_type="system"
            )

            system_prompt = format_prompt(user_state, str(dynamic_prompt))

            # Remove any existing SystemMessage and add the new one at the beginning
            updated_messages = [
                msg for msg in updated_messages if not isinstance(msg, SystemMessage)
            ]
            updated_messages.insert(0, SystemMessage(content=system_prompt))

            # Create updated state
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

     # Get the final state after processing
    final_state_snapshot: StateSnapshot = await main_graph.aget_state(
        configuration, subgraphs=True
    )
    final_state = innermost_subgraph_state(final_state_snapshot)
    messages = final_state.values.get("messages", [])
    response = messages[-1].content if messages else ""

    return response
