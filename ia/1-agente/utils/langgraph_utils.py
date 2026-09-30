import logging
from typing import Any
from utils.date_time import get_current_timestamp

# from utils.customer_data import CustomerData

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def log_state_and_last_message(state):
    """Log all variables in state and the last message in 'messages'."""
    logger.info("--- STATE VARIABLES ---")
    for key, value in state.items():
        if key != "messages":
            logger.info("%s : %s", key, value)

    if "messages" in state and state["messages"]:
        logger.info("Last message: %s", state["messages"][-1].content[:500])
    else:
        logger.debug("No messages found in state.")
    logger.debug("Finished: log_state_and_last_message")


def format_prompt(state, prompt_template: str) -> str:
    """ "Format prompt white state values"""
    system_prompt = prompt_template.format(
        document=state.get("document", "_None_"),
        userName=state.get("user_name", "_None_"),
        language=state.get("language", "_None_"),
        currentDate=get_current_timestamp(),
    )
    logger.debug("Finished: format_prompt: %s", system_prompt)
    return system_prompt


# async def update_state(state: AssistantState, tenant_id: str) -> AssistantState:
#     """Its for update last customer query in the state ???"""
#     assert state is not None, "update_state: State cannot be None"
#     assert tenant_id is not None, "update_state: tenant_id cannot be None"
#     customer_data = await CustomerData.create(tenant_id)
#     customer_document_id, customer_document_type, customer_user_name = (
#         await customer_data.get_last_customer_query_data(state["token"], tenant_id)
#     )
#     if customer_document_id != state["customer_document_id"]:
#         state["customer_document_id"] = customer_document_id
#         state["customer_document_type"] = customer_document_type
#         state["customer_user_name"] = customer_user_name
#     logger.debug("Finished: update_state")
#     return state

#     """Its for update last customer query in the state ???"""
#     assert state is not None, "update_state: State cannot be None"
#     assert tenant_id is not None, "update_state: tenant_id cannot be None"
#     customer_data = CustomerData(tenant_id)
#     customer_document_id, customer_document_type, customer_user_name = (
#         customer_data.get_last_customer_query_data(state["token"], tenant_id)
#     )
#     if customer_document_id != state["customer_document_id"]:
#         state["customer_document_id"] = customer_document_id
#         state["customer_document_type"] = customer_document_type
#         state["customer_user_name"] = customer_user_name
#     logger.debug("Finished: update_state")
#     return state


def load_tools_config(
    tools: list[dict[str, Any]], tenant_config, tenant_id: str, agent_config
):
    tool_list = []
    for tool in tools:
        try:
            structured_tool = tool["tool_class"](
                tenant_config, tenant_id
            ).get_structured_tool(
                tool["tool_name"], agent_config["tools"][tool["tool_name"]]
            )
            tool_list.append(structured_tool)
        except Exception:
            # logger.error("LangGraph_Utils - Error binding tool: %s - Error: ", tool["tool_name"], str(e))
            pass
    return tool_list
