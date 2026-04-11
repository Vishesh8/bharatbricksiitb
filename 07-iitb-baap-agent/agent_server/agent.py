import asyncio
import logging
import os
from datetime import datetime
from typing import AsyncGenerator, Optional

import litellm
import mlflow
from databricks.sdk import WorkspaceClient
from databricks_langchain import (
    ChatDatabricks,
    DatabricksMCPServer,
    DatabricksMultiServerMCPClient,
)
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

# Module-level cache for MCP tools only (expensive network calls)
# Prompt is loaded each request for MLflow linking
_cached_tools = None
_cache_lock = asyncio.Lock()

# Configuration from environment variables (set via databricks.yml)
CATALOG_NAME = os.environ.get("CATALOG_NAME", "dbdemos_vishesh")
SCHEMA_NAME = os.environ.get("SCHEMA_NAME", "bharat_bricks")
VECTOR_INDEX_NAME = os.environ.get("VECTOR_INDEX_NAME", "gold_posts_vs_index")
GENIE_SPACE_ID = os.environ.get("GENIE_SPACE_ID", "01f1294bf4441d919d11ea6b4796f9da")
PROMPT_NAME = os.environ.get("PROMPT_NAME", "iitb-lingo-prompt")
PROMPT_ALIAS = os.environ.get("PROMPT_ALIAS", "production")

# Construct derived configurations
PROMPT_REGISTRY_URI = f"prompts:/{CATALOG_NAME}.{SCHEMA_NAME}.{PROMPT_NAME}@{PROMPT_ALIAS}"

# Validation
REQUIRED_CONFIGS = {
    "CATALOG_NAME": CATALOG_NAME,
    "SCHEMA_NAME": SCHEMA_NAME,
    "VECTOR_INDEX_NAME": VECTOR_INDEX_NAME,
    "GENIE_SPACE_ID": GENIE_SPACE_ID,
}
missing = [k for k, v in REQUIRED_CONFIGS.items() if not v]
if missing:
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

logger.info(f"Agent configured with: {CATALOG_NAME}.{SCHEMA_NAME}, Vector Index: {VECTOR_INDEX_NAME}, Genie: {GENIE_SPACE_ID}")


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().isoformat()


def init_mcp_client(workspace_client: WorkspaceClient) -> DatabricksMultiServerMCPClient:
    """Initialize MCP client with Vector Search and Genie servers."""
    host_name = get_databricks_host_from_env()

    # Vector Search MCP Server for RAG
    vector_search_url = f"{host_name}/api/2.0/mcp/vector-search/{CATALOG_NAME}/{SCHEMA_NAME}/{VECTOR_INDEX_NAME}"
    vector_search_server = DatabricksMCPServer(
        name="iitb-posts-search",
        url=vector_search_url,
        workspace_client=workspace_client,
    )

    # Genie MCP Server for Analytics
    genie_url = f"{host_name}/api/2.0/mcp/genie/{GENIE_SPACE_ID}"
    genie_server = DatabricksMCPServer(
        name="iitb-analytics",
        url=genie_url,
        workspace_client=workspace_client,
    )

    return DatabricksMultiServerMCPClient([vector_search_server, genie_server])


async def get_or_init_tools():
    """Cache MCP tools (expensive network calls). Returns list of tools."""
    global _cached_tools

    if _cached_tools is not None:
        return _cached_tools

    async with _cache_lock:
        if _cached_tools is not None:  # Double-check after acquiring lock
            return _cached_tools

        mcp_client = init_mcp_client(sp_workspace_client)
        tools = [get_current_time]
        try:
            mcp_tools = await mcp_client.get_tools()
            tools.extend(mcp_tools)
            logger.info(f"Loaded {len(mcp_tools)} MCP tools: {[t.name for t in mcp_tools]}")
        except Exception as e:
            logger.warning(f"Failed to fetch MCP tools: {e}. Continuing without MCP tools.")

        _cached_tools = tools
        logger.info("MCP tools cached for subsequent requests")
        return tools


@invoke()
async def invoke_handler(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    outputs = [
        event.item
        async for event in stream_handler(request)
        if event.type == "response.output_item.done"
    ]
    return ResponsesAgentResponse(output=outputs)


@mlflow.trace(name="load_system_prompt")
def load_system_prompt(tools: list) -> str:
    """Load and format system prompt. Traced for MLflow prompt linking."""
    prompt = mlflow.genai.load_prompt(PROMPT_REGISTRY_URI)
    tool_descriptions = "\n".join([f"- **{t.name}**: {t.description}" for t in tools])
    return prompt.format(tools=tool_descriptions)


@stream()
async def stream_handler(
    request: ResponsesAgentRequest,
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    if session_id := get_session_id(request):
        mlflow.update_current_trace(metadata={"mlflow.trace.session": session_id})

    # Get cached tools (expensive MCP calls, reused)
    tools = await get_or_init_tools()

    # Load prompt inside traced function (enables MLflow prompt linking)
    system_prompt = load_system_prompt(tools)

    # Create agent with fresh prompt
    agent = create_agent(
        tools=tools,
        model=ChatDatabricks(
            endpoint="databricks-claude-sonnet-4-6",
            extra_body={"system": system_prompt},
        ),
    )

    mlflow.update_current_trace(metadata={"system_prompt": system_prompt})
    messages = {"messages": to_chat_completions_input([i.model_dump() for i in request.input])}

    async for event in process_agent_astream_events(
        agent.astream(input=messages, stream_mode=["updates", "messages"])
    ):
        yield event
