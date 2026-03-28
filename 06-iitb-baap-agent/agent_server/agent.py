import logging
import os
from datetime import datetime
from typing import AsyncGenerator, Optional

import litellm
import mlflow
from databricks.sdk import WorkspaceClient

# Configuration - override via environment variables (set in databricks.yml/app.yaml)
CATALOG = os.environ.get("DATABRICKS_CATALOG", "dbdemos_vishesh")
SCHEMA = os.environ.get("DATABRICKS_SCHEMA", "bharat_bricks")
GENIE_SPACE_ID = os.environ.get("GENIE_SPACE_ID", "01f1294bf4441d919d11ea6b4796f9da")
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

# IIT Bombay Campus Advisor System Prompt
SYSTEM_PROMPT = """You are the IIT Bombay Campus Advisor, a helpful AI assistant that answers questions about IIT Bombay campus life using community discussions from r/iitbombay.

You have access to the following tools:

1. **iitb-posts-search**: Search community discussions semantically using Vector Search.
   Use for questions about: experiences, opinions, advice, placements, hostel life, academics, clubs, techfest, inter-IIT, etc.

2. **iitb-analytics**: Query subreddit metrics and trends using Genie.
   Use for questions about: statistics, engagement metrics, trending topics, author activity, post counts, popular flairs.

## Guidelines

- **Always cite sources**: When sharing experiences or opinions from posts, mention the post title and author
- **Aggregate perspectives**: For opinion questions, gather multiple viewpoints and present a balanced summary
- **Be helpful**: Assist both prospective students (JEE aspirants) and current IIT Bombay junta
- **Use IITB slang naturally**: fundae, stud, junta, peace types, ghissu, machchis, insti, etc.
- **For analytics**: Use the Genie tool to query metrics like engagement, trending topics, author stats
- **Be honest**: If you can't find relevant information, say so rather than making things up

## Response Format

For experiential questions:
1. Search for relevant posts using iitb-posts-search
2. Summarize the key insights from community discussions
3. Cite specific posts with titles/authors
4. Add any relevant analytics if helpful

For analytics questions:
1. Use iitb-analytics to query the metrics
2. Present the data clearly
3. Provide context or insights based on the numbers

Remember: You're helping students navigate one of India's premier institutions. Be informative, friendly, and authentic to the IITB culture!
"""


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().isoformat()


def init_mcp_client(workspace_client: WorkspaceClient) -> DatabricksMultiServerMCPClient:
    """Initialize MCP client with Vector Search and Genie servers."""
    host_name = get_databricks_host_from_env()

    # Vector Search MCP Server for RAG
    vector_search_server = DatabricksMCPServer(
        name="iitb-posts-search",
        url=f"{host_name}/api/2.0/mcp/vector-search/{CATALOG}/{SCHEMA}/gold_posts_vs_index",
        workspace_client=workspace_client,
    )

    # Genie MCP Server for Analytics
    genie_server = DatabricksMCPServer(
        name="iitb-analytics",
        url=f"{host_name}/api/2.0/mcp/genie/{GENIE_SPACE_ID}",
        workspace_client=workspace_client,
    )

    return DatabricksMultiServerMCPClient([vector_search_server, genie_server])


async def init_agent(workspace_client: Optional[WorkspaceClient] = None):
    """Initialize the agent with MCP tools."""
    ws_client = workspace_client or sp_workspace_client
    mcp_client = init_mcp_client(ws_client)

    tools = [get_current_time]
    try:
        mcp_tools = await mcp_client.get_tools()
        tools.extend(mcp_tools)
        logger.info(f"Loaded {len(mcp_tools)} MCP tools: {[t.name for t in mcp_tools]}")
    except Exception as e:
        logger.warning(f"Failed to fetch MCP tools: {e}. Continuing without MCP tools.")

    return create_agent(
        tools=tools,
        model=ChatDatabricks(
            endpoint="databricks-claude-sonnet-4-6",
            extra_body={"system": SYSTEM_PROMPT},
        ),
    )


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

    agent = await init_agent()
    messages = {"messages": to_chat_completions_input([i.model_dump() for i in request.input])}

    async for event in process_agent_astream_events(
        agent.astream(input=messages, stream_mode=["updates", "messages"])
    ):
        yield event
