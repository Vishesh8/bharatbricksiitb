import asyncio
import logging
from datetime import datetime
from pathlib import Path
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

from agent_server.config import (
    GENIE_SPACE_ID,
    MODEL_ENDPOINT,
    PROMPT_REGISTRY_URI,
    VECTOR_SEARCH_INDEX,
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

# PROMPT_REGISTRY_URI is imported from config.py


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().isoformat()


def init_mcp_client(workspace_client: WorkspaceClient) -> DatabricksMultiServerMCPClient:
    """Initialize MCP client with Vector Search and Genie servers."""
    host_name = get_databricks_host_from_env()

    # Convert dotted index name to URL path (catalog.schema.index -> catalog/schema/index)
    vs_index_path = VECTOR_SEARCH_INDEX.replace(".", "/")

    # Vector Search MCP Server for RAG
    vector_search_server = DatabricksMCPServer(
        name="iitb-posts-search",
        url=f"{host_name}/api/2.0/mcp/vector-search/{vs_index_path}",
        workspace_client=workspace_client,
    )

    # Genie MCP Server for Analytics
    genie_server = DatabricksMCPServer(
        name="iitb-analytics",
        url=f"{host_name}/api/2.0/mcp/genie/{GENIE_SPACE_ID}",
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
            # Log at WARNING level to ensure it shows up in logs
            tool_names = [t.name for t in mcp_tools]
            print(f"[TOOLS] Loaded {len(mcp_tools)} MCP tools: {tool_names}", flush=True)
            logger.warning(f"MCP Tools loaded: {tool_names}")
        except Exception as e:
            print(f"[TOOLS ERROR] Failed to fetch MCP tools: {e}", flush=True)
            logger.warning(f"Failed to fetch MCP tools: {e}. Continuing without MCP tools.")

        _cached_tools = tools
        print(f"[TOOLS] Total tools available: {[t.name for t in tools]}", flush=True)
        return tools


@invoke()
async def invoke_handler(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    outputs = [
        event.item
        async for event in stream_handler(request)
        if event.type == "response.output_item.done"
    ]
    return ResponsesAgentResponse(output=outputs)


# Path to external system prompt file
SYSTEM_PROMPT_FILE = Path(__file__).parent / "SYSTEM_PROMPT.md"

# Inline fallback (last resort if file and registry both fail)
INLINE_FALLBACK_PROMPT = """You are the IIT Bombay Campus Advisor. Answer questions about IIT Bombay campus life using community discussions.

You have access to these tools:
{tools}

Use iitb-posts-search for opinions/experiences and iitb-analytics for statistics/trends.
Output plain conversational text (no markdown). Use IITB slang naturally (insti, junta, macha, etc.)."""


def _load_prompt_from_file() -> str | None:
    """Load system prompt from SYSTEM_PROMPT.md file."""
    try:
        if SYSTEM_PROMPT_FILE.exists():
            return SYSTEM_PROMPT_FILE.read_text()
        logger.warning(f"System prompt file not found: {SYSTEM_PROMPT_FILE}")
        return None
    except Exception as e:
        logger.warning(f"Failed to read system prompt file: {e}")
        return None


@mlflow.trace(name="load_system_prompt")
def load_system_prompt(tools: list) -> str:
    """Load and format system prompt. Priority: registry > file > inline fallback."""
    tool_descriptions = "\n".join([f"- {t.name}: {t.description}" for t in tools])

    # Try 1: Load from MLflow prompt registry
    try:
        prompt = mlflow.genai.load_prompt(PROMPT_REGISTRY_URI)
        logger.info("Loaded prompt from MLflow registry")
        return prompt.format(tools=tool_descriptions)
    except Exception as e:
        logger.warning(f"Failed to load prompt from registry: {e}")

    # Try 2: Load from SYSTEM_PROMPT.md file
    file_prompt = _load_prompt_from_file()
    if file_prompt:
        logger.info("Using prompt from SYSTEM_PROMPT.md file")
        return file_prompt.format(tools=tool_descriptions)

    # Try 3: Use inline fallback
    logger.warning("Using inline fallback prompt")
    return INLINE_FALLBACK_PROMPT.format(tools=tool_descriptions)


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
            endpoint=MODEL_ENDPOINT,
            extra_body={"system": system_prompt},
        ),
    )

    mlflow.update_current_trace(metadata={"system_prompt": system_prompt})
    messages = {"messages": to_chat_completions_input([i.model_dump() for i in request.input])}

    async for event in process_agent_astream_events(
        agent.astream(input=messages, stream_mode=["updates", "messages"])
    ):
        yield event
