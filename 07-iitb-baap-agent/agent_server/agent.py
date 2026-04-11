import asyncio
import json
import logging
import time
import uuid
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
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from mlflow.genai.agent_server import invoke, stream
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    output_to_responses_items_stream,
    to_chat_completions_input,
)

from agent_server.config import (
    GENIE_SPACE_ID,
    MODEL_ENDPOINT,
    VECTOR_SEARCH_INDEX,
)
from agent_server.utils import (
    get_databricks_host_from_env,
    get_session_id,
    process_agent_astream_events,
)

logger = logging.getLogger(__name__)
mlflow.langchain.autolog()
logging.getLogger("mlflow.utils.autologging_utils").setLevel(logging.ERROR)
litellm.suppress_debug_info = True

# =============================================================================
# Hardcoded system prompt (avoids .format() curly-brace issues and file/registry fragility)
# =============================================================================

_PROMPT_ROLE = """You are the IIT Bombay Campus Advisor, a helpful AI assistant that answers questions about IIT Bombay campus life using community discussions from r/iitbombay.

You have access to two tools: a vector search over student posts and a Genie analytics space. Both have ALREADY been called for you -- their results are in the conversation history above.

RULES:
- Use the pre-fetched tool results to compose your answer. They almost always have what you need.
- Only make ADDITIONAL tool calls if the pre-fetched results are clearly insufficient for the specific question asked.
- If you do call tools, call them in parallel (both at once, not sequentially).
- Do NOT decompose the question into sub-queries -- answer from what you have.
- Maximum 1-2 follow-up tool calls if truly needed.
- NEVER tell the user to "standby", "wait", or that you'll "follow up". Deliver your COMPLETE answer NOW."""

_PROMPT_FORMAT = """
## Response Format

Format your responses using **markdown** for readability. The chat interface fully supports rich formatting.

### Formatting guidelines:
- Use **bold** for emphasis and key takeaways
- Use bullet points and numbered lists to organize information
- Use > blockquotes when quoting actual student posts
- Use ### headers to separate major sections when the answer is long
- Keep paragraphs short (2-3 sentences max)
- End with a brief takeaway or summary when appropriate

CRITICAL: NEVER tell the user to "wait", "standby", or that you'll "follow up".
You must deliver your COMPLETE, FINAL answer in a single response. Do not
announce that you are processing or compiling -- just provide the answer directly.

### Tone and style:
- Conversational and friendly, like a senior advising a freshie
- Use IITB slang naturally when it fits (don't force it)
- Cite sources when possible (post titles, authors, data points)
- Aggregate multiple perspectives for opinion questions
- Be helpful to both JEE aspirants and current students"""

_PROMPT_SLANG = """
## IITB Slang Glossary (use these naturally)

**Suffixes:** -aap(a) (emphasis), -(a)u (adjective: machau, cracku), -giri (act of: RG-giri), -max/-maxx (superlative: crackmax, godmax), -aax (IITBism: peaceaax)

**Academic:** mug (cram), muggoo (studious person), farra (FR grade), crack/faadu (excellent), RG (grade saboteur), cts/CTs (clearing tensions), fight (try hard), app (go abroad), schol (scholarship), suck (email profs for research)

**People:** freshie (1st yr), sophie (2nd yr), dadda/daddi (DD students), matka/matki (MTech), junta (everyone), bandi (girl), coordie (coordinator), orgie (organizer), stud (expert), fartoo (BS-er), despo (desperate), panchii/punter (any person)

**Campus:** insti (IIT Bombay), dep (department), liby (library), SAC (Student Activity Center), YP (Y-Point), Shack (Coffee Shack), convo (Convocation Hall), LT (Lecture Theatre), MB (Main Building), tumtum (campus bus), khopcha (hangout spots), gaddha (hill base area)

**Emotions:** peace/peaceful (relief), tension (stress), nbd/nabard (nervous breakdown), daya (sarcastic pity), give-up (hopeless), nightout (all-nighter), crash (sleep), freakout (enjoy)

**Actions:** chamka (understood), chamkaa (explain), arbit (random/weird), enthu (enthusiastic), lukkha (time-pass), jugaad (workaround), ditch (abandon), kat (lose out), macha (crack infinitely - MACHAXX!), fart (BS), god/godmax (awesome), cog (copy), hog (eat eagerly), scope (no chance)

**Quantities:** infi/infinite (>2), delta (a little), hazaar (a lot), generaal (average), obscene (extreme amount)

**Food:** grub (food from home), breaker (breakfast), mess (dining hall), chinco (Chinese restaurant outside H-8)

**Admin:** DoSA (Dean of Student Affairs), diro (Director), HOD (Head of Dept), DAC (Disciplinary Action Committee)

**Sports:** baddy (badminton), basky (basketball), footer (football), volley (volleyball)

**Other:** funda(e) (fundamentals), fundoo (worthwhile), gyaan (wisdom from seniors), pseud (classy), shady (not right), boss (casual address), ok types (went well), sorry rahega (won't happen), khaach (cancel/destroy)"""


def build_system_prompt(tools: list | None = None) -> str:
    """Build the full system prompt via concatenation (no .format() needed)."""
    parts = [_PROMPT_ROLE, _PROMPT_FORMAT, _PROMPT_SLANG]
    if tools:
        descs = "\n".join(f"- **{t.name}**: {t.description}" for t in tools if t.description)
        parts.insert(1, f"## Available Tools\n\n{descs}")
    return "\n\n".join(parts)


# =============================================================================
# Workspace client & MCP tool caching
# =============================================================================

_sp_workspace_client: Optional[WorkspaceClient] = None


def _get_sp_workspace_client() -> WorkspaceClient:
    global _sp_workspace_client
    if _sp_workspace_client is None:
        _sp_workspace_client = WorkspaceClient()
    return _sp_workspace_client


_cached_tools = None
_cache_lock = asyncio.Lock()
_cache_timestamp: float = 0
_CACHE_TTL_SECONDS = 300


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().isoformat()


def init_mcp_client(workspace_client: WorkspaceClient) -> DatabricksMultiServerMCPClient:
    host_name = get_databricks_host_from_env(workspace_client)
    vs_index_path = VECTOR_SEARCH_INDEX.replace(".", "/")

    vector_search_server = DatabricksMCPServer(
        name="iitb-posts-search",
        url=f"{host_name}/api/2.0/mcp/vector-search/{vs_index_path}",
        workspace_client=workspace_client,
    )
    genie_server = DatabricksMCPServer(
        name="iitb-analytics",
        url=f"{host_name}/api/2.0/mcp/genie/{GENIE_SPACE_ID}",
        workspace_client=workspace_client,
    )

    return DatabricksMultiServerMCPClient([vector_search_server, genie_server])


async def get_or_init_tools():
    """Fetch MCP tools, caching for _CACHE_TTL_SECONDS to keep names fresh."""
    global _cached_tools, _cache_timestamp, _cached_agent

    now = time.monotonic()
    if _cached_tools is not None and now - _cache_timestamp < _CACHE_TTL_SECONDS:
        return _cached_tools

    async with _cache_lock:
        now = time.monotonic()
        if _cached_tools is not None and now - _cache_timestamp < _CACHE_TTL_SECONDS:
            return _cached_tools

        # Invalidate the cached agent graph so it rebuilds with fresh tools
        _cached_agent = None

        ws = _get_sp_workspace_client()
        mcp_client = init_mcp_client(ws)
        tools = [get_current_time]
        try:
            mcp_tools = await mcp_client.get_tools()
            tools.extend(mcp_tools)
            tool_names = [t.name for t in mcp_tools]
            logger.info(f"Loaded {len(mcp_tools)} MCP tools: {tool_names}")
        except Exception as e:
            logger.warning(f"Failed to fetch MCP tools: {e}")

        _cached_tools = tools
        _cache_timestamp = time.monotonic()
        logger.info(f"Total tools available: {[t.name for t in tools]}")
        return tools


# =============================================================================
# Pre-fetch both tools and inject as visible tool-call messages
# =============================================================================

_VS_TOOL_NAME = VECTOR_SEARCH_INDEX.replace(".", "__")
_GENIE_TOOL_NAME = f"query_space_{GENIE_SPACE_ID}"


def _find_tool_by_name(tools: list, name: str):
    for t in tools:
        if t.name == name:
            return t
    return None


@mlflow.trace(name="pre_fetch_tools")
async def pre_fetch_as_messages(user_query: str, tools: list) -> list:
    """Call both VS and Genie in parallel, return LangChain messages that make them visible in the UI."""
    vs_tool = _find_tool_by_name(tools, _VS_TOOL_NAME)
    genie_tool = _find_tool_by_name(tools, _GENIE_TOOL_NAME)

    if vs_tool is None:
        logger.warning(f"VS tool '{_VS_TOOL_NAME}' not found, falling back to prefix search")
        vs_tool = next((t for t in tools if t.name.startswith("iitb__bharat_bricks__vs_")), None)
    if genie_tool is None:
        logger.warning(f"Genie tool '{_GENIE_TOOL_NAME}' not found, falling back to prefix search")
        genie_tool = next((t for t in tools if t.name.startswith("query_space_")), None)

    results = {}

    async def call_tool(name, tool_obj, args):
        if tool_obj is None:
            return
        try:
            result = await tool_obj.ainvoke(args)
            results[name] = {"result": result, "tool": tool_obj}
        except Exception as e:
            logger.warning(f"{name} pre-fetch failed: {e}")
            results[name] = {"result": f"Error: {e}", "tool": tool_obj}

    await asyncio.gather(
        call_tool("vs", vs_tool, {"query": user_query}),
        call_tool("genie", genie_tool, {"query": user_query}),
    )

    if not results:
        return []

    tool_calls = []
    tool_messages = []

    for key, data in results.items():
        call_id = f"prefetch_{key}_{uuid.uuid4().hex[:8]}"
        tool_obj = data["tool"]
        raw_result = data["result"]

        if isinstance(raw_result, str):
            content = raw_result
        else:
            content = json.dumps(raw_result, default=str)

        tool_calls.append({
            "id": call_id,
            "name": tool_obj.name,
            "args": {"query": user_query},
        })
        tool_messages.append(ToolMessage(content=content, tool_call_id=call_id))

    ai_msg = AIMessage(content="", tool_calls=tool_calls)
    return [ai_msg] + tool_messages


# =============================================================================
# Cached agent graph (reused across requests since tools + prompt are stable)
# =============================================================================

_cached_agent = None
_cached_agent_lock = asyncio.Lock()


async def get_or_create_agent(tools: list):
    """Return a cached compiled agent graph, rebuilding only when tools change."""
    global _cached_agent

    if _cached_agent is not None:
        return _cached_agent

    async with _cached_agent_lock:
        if _cached_agent is not None:
            return _cached_agent

        system_prompt = build_system_prompt(tools)
        agent = create_agent(
            tools=tools,
            model=ChatDatabricks(
                endpoint=MODEL_ENDPOINT,
                extra_body={"system": system_prompt},
            ),
        )
        _cached_agent = (agent, system_prompt)
        logger.info("Compiled and cached agent graph")
        return _cached_agent


# =============================================================================
# Handlers
# =============================================================================

_AGENT_CONFIG = {"recursion_limit": 8}


@invoke()
async def invoke_handler(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    outputs = [
        event.item
        async for event in stream_handler(request)
        if event.type == "response.output_item.done"
    ]
    return ResponsesAgentResponse(output=outputs)


def _extract_last_user_query(request: ResponsesAgentRequest) -> str:
    for item in reversed(request.input):
        item_dict = item.model_dump() if hasattr(item, "model_dump") else item
        if item_dict.get("role") == "user":
            content = item_dict.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "input_text":
                        return part.get("text", "")
    return ""


@stream()
async def stream_handler(
    request: ResponsesAgentRequest,
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    if session_id := get_session_id(request):
        mlflow.update_current_trace(metadata={"mlflow.trace.session": session_id})

    tools = await get_or_init_tools()
    user_query = _extract_last_user_query(request)
    original_messages = to_chat_completions_input([i.model_dump() for i in request.input])

    has_prior_tool_results = any(
        getattr(m, "role", None) == "tool" or isinstance(m, ToolMessage)
        for m in original_messages
    )

    if has_prior_tool_results:
        logger.info("Follow-up turn detected, skipping prefetch")
        prefetch_messages = []
    else:
        prefetch_messages = await pre_fetch_as_messages(user_query, tools)

    for msg in prefetch_messages:
        for item in output_to_responses_items_stream([msg]):
            yield item

    agent, system_prompt = await get_or_create_agent(tools)

    mlflow.update_current_trace(metadata={"system_prompt": system_prompt[:2000]})
    messages = {"messages": original_messages + prefetch_messages}

    async for event in process_agent_astream_events(
        agent.astream(input=messages, stream_mode=["updates", "messages"], config=_AGENT_CONFIG)
    ):
        yield event
