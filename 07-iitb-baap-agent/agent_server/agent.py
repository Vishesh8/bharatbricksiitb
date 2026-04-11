import logging
import os
from datetime import datetime
from typing import AsyncGenerator, Optional

import litellm
import mlflow
import mlflow.genai
from databricks.sdk import WorkspaceClient
from databricks_langchain import ChatDatabricks, DatabricksMCPServer, DatabricksMultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.tools import tool
from mlflow.genai.agent_server import invoke, stream
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    to_chat_completions_input,
)

from agent_server.utils import (
    get_databricks_host_from_env,
    get_session_id,
    get_user_workspace_client,
    process_agent_astream_events,
)

logger = logging.getLogger(__name__)
mlflow.langchain.autolog()
logging.getLogger("mlflow.utils.autologging_utils").setLevel(logging.ERROR)
litellm.suppress_debug_info = True
sp_workspace_client = WorkspaceClient()

# Configuration from environment variables
MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT", "databricks-claude-sonnet-4")
SYSTEM_PROMPT_NAME = os.getenv("SYSTEM_PROMPT_NAME")
GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID")
VECTOR_SEARCH_INDEX = os.getenv("VECTOR_SEARCH_INDEX")  # format: catalog.schema.index_name

# Load system prompt from UC Prompt Registry (if configured)
SYSTEM_PROMPT = None
if SYSTEM_PROMPT_NAME:
    try:
        _prompt_template = mlflow.genai.load_prompt(f"prompts:/{SYSTEM_PROMPT_NAME}")
        SYSTEM_PROMPT = _prompt_template.format(
            tools="Genie (for analytics queries) and Vector Search (for finding relevant community posts)"
        )
        logger.info(f"Loaded system prompt: {SYSTEM_PROMPT_NAME}")
    except Exception as e:
        logger.warning(f"Failed to load prompt {SYSTEM_PROMPT_NAME}: {e}")


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().isoformat()


def init_mcp_client(workspace_client: WorkspaceClient) -> DatabricksMultiServerMCPClient:
    host_name = get_databricks_host_from_env()
    servers = []

    # Add Genie Space if configured
    if GENIE_SPACE_ID:
        servers.append(DatabricksMCPServer(
            name="genie",
            url=f"{host_name}/api/2.0/mcp/genie/{GENIE_SPACE_ID}",
            workspace_client=workspace_client,
        ))
        logger.info(f"Added Genie MCP server: {GENIE_SPACE_ID}")

    # Add Vector Search if configured (parse catalog.schema.index_name)
    if VECTOR_SEARCH_INDEX:
        parts = VECTOR_SEARCH_INDEX.split(".")
        if len(parts) == 3:
            catalog, schema, index_name = parts
            servers.append(DatabricksMCPServer(
                name="vector-search",
                url=f"{host_name}/api/2.0/mcp/vector-search/{catalog}/{schema}/{index_name}",
                workspace_client=workspace_client,
            ))
            logger.info(f"Added Vector Search MCP server: {VECTOR_SEARCH_INDEX}")
        else:
            logger.warning(f"Invalid VECTOR_SEARCH_INDEX format: {VECTOR_SEARCH_INDEX}. Expected: catalog.schema.index_name")

    return DatabricksMultiServerMCPClient(servers)


async def init_agent(workspace_client: Optional[WorkspaceClient] = None):
    tools = [get_current_time]

    # Add MCP tools (Genie + Vector Search) if configured
    mcp_client = init_mcp_client(workspace_client or sp_workspace_client)
    try:
        mcp_tools = await mcp_client.get_tools()
        tools.extend(mcp_tools)
        logger.info(f"Loaded {len(mcp_tools)} MCP tools")
    except Exception:
        logger.warning("Failed to fetch MCP tools. Continuing without MCP tools.", exc_info=True)

    return create_agent(tools=tools, model=ChatDatabricks(endpoint=MODEL_ENDPOINT))


@invoke()
async def invoke_handler(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    outputs = [
        event.item
        async for event in stream_handler(request)
        if event.type == "response.output_item.done"
    ]
    return ResponsesAgentResponse(output=outputs)


@stream()
async def stream_handler(
    request: ResponsesAgentRequest,
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    if session_id := get_session_id(request):
        mlflow.update_current_trace(metadata={"mlflow.trace.session": session_id})

    # By default, uses service principal credentials.
    # For on-behalf-of user authentication, use get_user_workspace_client() instead:
    #   agent = await init_agent(workspace_client=get_user_workspace_client())
    agent = await init_agent()

    # Get user messages
    user_messages = to_chat_completions_input([i.model_dump() for i in request.input])

    # Prepend system prompt if configured
    if SYSTEM_PROMPT:
        all_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_messages
    else:
        all_messages = user_messages

    messages = {"messages": all_messages}

    async for event in process_agent_astream_events(
        agent.astream(input=messages, stream_mode=["updates", "messages"])
    ):
        yield event
