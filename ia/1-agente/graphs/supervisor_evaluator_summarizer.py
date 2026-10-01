import logging
from typing import List, Literal

from langgraph_supervisor import create_supervisor
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)

from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from graphs.assistant_state import EvaluatorState
from openevals.llm import create_async_llm_as_judge

# Redis or Mongo-based persistence for production use
# from langgraph.checkpoint.redis import RedisSaver
# from langgraph.store.redis import RedisStore
# from langgraph.checkpoint.mongodb import MongoDBSaver

# For Graphs
from langgraph.graph import END, StateGraph, START
from graphs.assistant_state import AssistantState
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

# For using InMemory checkpointer and store
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

# Dynamic agents are loaded from configuration

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Starting: supervisor")


class Grade(TypedDict):
    """Evaluation of the response."""

    grade: Literal["PASS", "FAIL"]


async def create_supervisor_workflow(
    available_llms,
    tenant_id,
    state: dict,
    supervisor_name: str,
    agents_list: list,
    handoff_tools: list,
):
    """
    Centralized method for creating supervisors.

    Args:
        available_llms: Dictionary of available LLM models
        tenant_id: Tenant ID
        state: User state
        supervisor_name: Supervisor name (to get a dynamic prompt)
        agents_list: List of agents for the supervisor

    Returns:
        Compiled supervisor workflow
    """
    # Get dynamic supervisor prompt from S3
    supervisor_prompt = None

    if tenant_id:
        try:
            from utils.tenant_config import get_agent_prompt

            dynamic_prompt = await get_agent_prompt(
                tenant_id, supervisor_name, prompt_type="system"
            )
            if isinstance(dynamic_prompt, str) and dynamic_prompt.strip():
                supervisor_prompt = dynamic_prompt
            else:
                logger.error(
                    f"No dynamic supervisor prompt found for {supervisor_name} in S3. Stopping execution."
                )
                raise Exception(
                    f"No dynamic supervisor found for {supervisor_name} in S3."
                )

        except Exception as e:
            logger.error(f"Error getting supervisor prompt for {supervisor_name}: {e}")
            raise

    # Create supervisor workflow
    workflow = create_supervisor(
        agents_list,
        tools=handoff_tools,
        model=available_llms["gpt-4.1-mini"],
        output_mode="full_history",  # "last_message", "full_history",
        add_handoff_messages=False,  # Add handoff tool invocations to the history
        prompt=supervisor_prompt,
    )
    return workflow.compile()


async def instantiate_supervisor(available_llms, tenant_id, state: dict = {}):
    """Creates a supervisor agent that controls all other agents."""

    if not tenant_id:
        raise Exception("tenant_id is required for dynamic supervisor creation")

    try:
        # Cargar agentes dinámicos
        from utils.agents import (
            create_dynamic_agents_from_config,
            get_all_available_tools,
        )

        available_tools = await get_all_available_tools()
        dynamic_agents_dict = await create_dynamic_agents_from_config(
            tenant_id, available_llms, available_tools
        )
        dynamic_agents = list(dynamic_agents_dict.values())
        logger.info(f"Se cargaron {len(dynamic_agents)} agentes dinámicos")

        # Crear supervisor dinámico - pasar todos los agentes disponibles
        # El supervisor filtrará los agentes según su configuración
        from utils.agents import create_dynamic_supervisors_from_config

        supervisors_dict = await create_dynamic_supervisors_from_config(
            tenant_id, available_llms, dynamic_agents
        )

        if "supervisor" not in supervisors_dict:
            raise Exception(
                "Supervisor 'supervisor' not found in dynamic configuration"
            )

        supervisor = supervisors_dict["supervisor"]
        return supervisor.compile()

    except Exception as e:
        logger.error(f"Error creating dynamic supervisor: {e}")
        raise


async def instantiate_supervisor_anonymous(available_llms, tenant_id, state: dict = {}):
    """Creates a supervisor anonymous agent that controls all other agents."""

    if not tenant_id:
        raise Exception("tenant_id is required for dynamic supervisor creation")

    try:
        from utils.agents import (
            create_dynamic_agents_from_config,
            get_all_available_tools,
            create_dynamic_supervisors_from_config,
        )

        available_tools = await get_all_available_tools()
        dynamic_agents_dict = await create_dynamic_agents_from_config(
            tenant_id, available_llms, available_tools
        )

        dynamic_agents = list(dynamic_agents_dict.values())
        logger.info(f"Se cargaron {len(dynamic_agents)} agentes dinámicos")

        supervisors_dict = await create_dynamic_supervisors_from_config(
            tenant_id, available_llms, dynamic_agents
        )

        if "supervisor_anon" not in supervisors_dict:
            raise Exception(
                "Supervisor 'supervisor_anon' not found in dynamic configuration"
            )

        supervisor = supervisors_dict["supervisor_anon"]
        return supervisor.compile()

    except Exception as e:
        logger.error(f"Error creating dynamic anonymous supervisor: {e}")
        raise


async def instantiate_supervisor_by_role(
    available_llms, tenant_id, state: dict = {}, role: str = "associate"
):
    """Creates a role-based supervisor. Uses supervisor_<role> key from dynamic config."""

    if not tenant_id:
        raise Exception("tenant_id is required for dynamic supervisor creation")

    supervisor_key = f"supervisor_{role}"

    try:
        from utils.agents import (
            create_dynamic_agents_from_config,
            get_all_available_tools,
            create_dynamic_supervisors_from_config,
        )

        available_tools = await get_all_available_tools()
        dynamic_agents_dict = await create_dynamic_agents_from_config(
            tenant_id, available_llms, available_tools
        )

        dynamic_agents = list(dynamic_agents_dict.values())
        logger.info(f"Se cargaron {len(dynamic_agents)} agentes dinámicos para rol '{role}'")

        supervisors_dict = await create_dynamic_supervisors_from_config(
            tenant_id, available_llms, dynamic_agents
        )

        if supervisor_key not in supervisors_dict:
            raise Exception(
                f"Supervisor '{supervisor_key}' not found in dynamic configuration"
            )

        supervisor = supervisors_dict[supervisor_key]
        return supervisor.compile()

    except Exception as e:
        logger.error(f"Error creating supervisor for role '{role}': {e}")
        raise


async def evaluator_node(
    state: EvaluatorState,
    tenant_id=None,
    evaluator_model=None,
    supervisor_node: str = "supervisor",
) -> Command[Literal["supervisor", "supervisor_anon", END]]:
    # Obtener prompt dinámico para el evaluador desde S3
    evaluator_prompt = None
    if tenant_id:
        try:
            from utils.tenant_config import get_agent_prompt

            dynamic_prompt = await get_agent_prompt(
                tenant_id, "evaluator_prompt.md", prompt_type="system"
            )
            if isinstance(dynamic_prompt, str) and dynamic_prompt.strip():
                evaluator_prompt = dynamic_prompt
            else:
                logger.error(
                    f"No dynamic evaluator prompt found for {tenant_id} in S3. Stopping execution."
                )
                raise Exception(
                    f"No dynamic evaluator prompt found for {tenant_id} in S3."
                )
        except Exception as e:
            logger.error(f"Error getting dynamic evaluator prompt for {tenant_id}: {e}")
            raise
    else:
        logger.error("No tenant_id provided for evaluator prompt. Stopping execution.")
        raise Exception("No tenant_id provided for evaluator prompt.")

    evaluator = create_async_llm_as_judge(
        prompt=evaluator_prompt,
        judge=evaluator_model,
    )
    # Prepare inputs and outputs for the evaluator
    # Here, we assume the last HumanMessage is the input, and the last AIMessage is the output
    messages = state["messages"]
    user_msg = next(
        (
            m.content
            for m in reversed(messages)
            if m.__class__.__name__ == "HumanMessage"
        ),
        None,
    )
    ai_msg = next(
        (m.content for m in reversed(messages) if m.__class__.__name__ == "AIMessage"),
        None,
    )
    if user_msg is None or ai_msg is None:
        # Fallback: skip evaluation if not enough context
        return Command(update={"trial": state["trial"] + 1}, goto=END)
    # Run the evaluator
    result = await evaluator(inputs=user_msg, outputs=ai_msg)
    logger.debug("Trial: %d, EvalResult: %s", state["trial"], result)
    # Interpret the result (score: True/False or 1/0)
    passed = result.get("score", False)
    if passed or state["trial"] > 2:
        return Command(update={"trial": state["trial"] + 1}, goto="summarizer")
    else:
        return Command(update={"trial": state["trial"] + 1}, goto=supervisor_node)


async def create_summarizer_node(model, tenant_id):
    # Get dynamic summarizer prompt from S3
    summarizer_prompt = None
    if tenant_id:
        try:
            from utils.tenant_config import get_agent_prompt

            dynamic_prompt = await get_agent_prompt(
                tenant_id, "summarizer_prompt.md", prompt_type="system"
            )
            if isinstance(dynamic_prompt, str) and dynamic_prompt.strip():
                summarizer_prompt = dynamic_prompt
            else:
                logger.error(
                    f"No dynamic summarizer prompt found for {tenant_id} in S3. Stopping execution."
                )
                raise Exception(
                    f"No dynamic summarizer prompt found for {tenant_id} in S3."
                )
        except Exception as e:
            logger.error(
                f"Error getting dynamic summarizer prompt for {tenant_id}: {e}"
            )
            raise
    else:
        logger.error("No tenant_id provided for summarizer prompt. Stopping execution.")
        raise Exception("No tenant_id provided for summarizer prompt.")
    prompt_template = ChatPromptTemplate(
        [
            ("system", summarizer_prompt),
            MessagesPlaceholder("msgs"),
            HumanMessage(content="Give the final response to the user."),
        ]
    )
    chain = prompt_template | model

    async def summarizer_node(state: AssistantState) -> AssistantState:
        response = await chain.ainvoke({"msgs": state["messages"]})
        logger.debug(
            "Response: %s", type(response)
        )  # 'langchain_core.messages.ai.AIMessage'
        logger.debug("Response: %s", response)
        return {"messages": [response]}

    return summarizer_node


async def create_graph(
    available_llms,
    tenant_id,
    state: dict = {},
    supervisor: CompiledStateGraph = None,
    supervisor_node: str = "supervisor",
) -> CompiledStateGraph:

    try:
        workflow = StateGraph(EvaluatorState)

        evaluator_model = available_llms.get("evaluator") or available_llms.get("default")
        summarizer_model = available_llms.get("default")

        async def evaluator(state):
            return await evaluator_node(state, tenant_id, evaluator_model, supervisor_node)

        summarizer = await create_summarizer_node(
            summarizer_model, tenant_id
        )

        # Nodes
        workflow.add_node(supervisor_node, supervisor)
        workflow.add_node("evaluator", evaluator)
        workflow.add_node("summarizer", summarizer)
        # Edges
        workflow.add_edge(START, supervisor_node)
        workflow.add_edge(supervisor_node, "evaluator")
        workflow.add_edge("summarizer", END)

        # In memory checkpointer
        checkpointer = InMemorySaver()
        store = InMemoryStore()

        # Compile and run
        app = workflow.compile(checkpointer=checkpointer, store=store)
        return app

    except Exception as e:
        logger.exception("Error while compile Graph")
        raise
