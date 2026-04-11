# IITB BAAP Agent

**IIT Bombay Campus Advisor** — an agentic RAG chatbot that answers questions about IIT Bombay campus life using r/iitbombay Reddit data, powered by Databricks Apps, LangGraph, Vector Search, and Genie.

---

## Overview

The BAAP Agent (Bharat Bricks Agentic App) combines two retrieval tools in a LangGraph agent:

| Tool | Source | Purpose |
|------|--------|---------|
| **Vector Search** | `iitb.bharat_bricks.vs_gold_posts_index` | Semantic search over ~1,300 Reddit posts |
| **Genie Space** | `IITB Junta Analytics` | SQL analytics queries for metrics and trends |

On every new user message, both tools are **pre-fetched in parallel** and injected into the conversation before the LLM responds — minimising latency and unnecessary follow-up tool calls.

---

## Architecture

```
Browser / Chat UI (React)
        │  HTTP (port 3000)
        ▼
  FastAPI Backend  ──► MLflow Tracing
        │
   LangGraph Agent
    ├── Pre-fetch (parallel)
    │     ├── Vector Search MCP  ──► iitb.bharat_bricks.vs_gold_posts_index
    │     └── Genie MCP          ──► IITB Junta Analytics Genie Space
    └── LLM (Qwen3-80B via Databricks Model Serving)
```

The entire stack runs as a **single Databricks App** — the `start-app` script launches the FastAPI server and the React frontend simultaneously, reporting ready only when both are up.

---

## Project Structure

```
07-iitb-baap-agent/
├── agent_server/
│   ├── agent.py           # LangGraph agent, MCP client, pre-fetch logic, stream/invoke handlers
│   ├── config.py          # Environment-variable-based configuration
│   ├── evaluate_agent.py  # MLflow evaluation with ConversationSimulator
│   ├── start_server.py    # Uvicorn/FastAPI entrypoint
│   └── utils.py           # Helpers (session ID extraction, stream event processing)
├── scripts/
│   ├── start_app.py       # Starts backend + frontend concurrently
│   ├── preflight.py       # Pre-deployment smoke test
│   └── discover_tools.py  # Lists available MCP tools
├── e2e-chatbot-app-next/  # React chat frontend (auto-cloned if missing)
├── app.yaml               # Databricks App config (command + env vars)
├── databricks.yml         # Databricks Asset Bundle (resources + targets)
└── pyproject.toml         # Python dependencies and script entrypoints
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Agent | LangGraph, LangChain, `databricks-langchain` |
| Tools | Databricks MCP (Vector Search + Genie) via `DatabricksMultiServerMCPClient` |
| LLM | `databricks-qwen3-next-80b-a3b-instruct` (configurable) |
| Observability | MLflow 3 (auto-log + traces + sessions) |
| Frontend | React (`e2e-chatbot-app-next`) with SSE streaming |
| Packaging | `uv` (Python), `npm` (frontend) |
| Deployment | Databricks Asset Bundle (`databricks.yml`) |

---

## Prerequisites

- **Databricks workspace** with Unity Catalog
- **Vector Search index** synced: `iitb.bharat_bricks.vs_gold_posts_index` (from `06-create-vector-index.ipynb`)
- **Genie Space** deployed: `IITB Junta Analytics` (from `05-iitb-junta-analytics-genie/`)
- **Local tools**: Python 3.11+, [`uv`](https://docs.astral.sh/uv/), Node.js 18+, Databricks CLI v0.205.0+

---

## Local Development

### 1. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```bash
# .env
DATABRICKS_CONFIG_PROFILE=DEFAULT          # or your CLI profile name
DATABRICKS_CATALOG=iitb
DATABRICKS_SCHEMA=bharat_bricks
GENIE_SPACE_ID=<your_genie_space_id>
VECTOR_SEARCH_INDEX=iitb.bharat_bricks.vs_gold_posts_index
MODEL_ENDPOINT=databricks-qwen3-next-80b-a3b-instruct
MLFLOW_EXPERIMENT_ID=<your_experiment_id>
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Run pre-flight check

Smoke-tests the backend end-to-end before you commit time to deployment:

```bash
uv run preflight
```

This starts the server on a random port, hits `/health`, sends a test message to `/invocations`, and shuts down.

### 4. Start the app

```bash
uv run start-app
```

This will:
1. Install and build the React frontend (cached on subsequent runs)
2. Start the FastAPI backend on **port 8000**
3. Start the React frontend on **port 3000**
4. Print `✓ Both frontend and backend are ready!` when both are up

Open **http://localhost:3000** in your browser.

To run the backend only (no UI):

```bash
uv run start-app --no-ui
```

---

## Deployment to Databricks Apps

### Using Databricks Asset Bundle (recommended)

```bash
# Authenticate
databricks configure --token

# Deploy to dev
databricks bundle deploy --target dev

# Start the app
databricks bundle run --target dev iitb_baap_agent
```

The bundle configures:
- App name: `iitb-baap-agent`
- MLflow experiment access (`CAN_MANAGE`)
- Vector Search index access (`SELECT`)
- Genie Space access (`CAN_RUN`)

> **Note:** MLflow Prompt Registry requires `EXECUTE` and `CREATE_FUNCTION` on the schema. Grant these manually if needed:
> ```bash
> databricks grants update schema iitb.bharat_bricks \
>   --json '{"changes":[{"principal":"<app-service-principal>","add":["EXECUTE","CREATE_FUNCTION"]}]}'
> ```

### Adapting to a different workspace

Update `databricks.yml` with your catalog, schema, Genie Space ID, vector index, and workspace host. Update the same values in `app.yaml` env section.

---

## Configuration Reference

All configuration is loaded from environment variables (`.env` locally, `app.yaml`/`databricks.yml` in production):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABRICKS_CATALOG` | `iitb` | Unity Catalog catalog name |
| `DATABRICKS_SCHEMA` | `bharat_bricks` | Schema containing tables and indexes |
| `GENIE_SPACE_ID` | *(see app.yaml)* | Genie Space ID for analytics queries |
| `VECTOR_SEARCH_INDEX` | `iitb.bharat_bricks.vs_gold_posts_index` | Full 3-part name of the VS index |
| `MODEL_ENDPOINT` | `databricks-qwen3-next-80b-a3b-instruct` | Databricks model serving endpoint |
| `MLFLOW_EXPERIMENT_ID` | *(from bundle)* | MLflow experiment for traces |
| `API_PROXY` | `http://localhost:8000/invocations` | Frontend → backend proxy URL |
| `CHAT_APP_PORT` | `3000` | Port for the React frontend |
| `CHAT_PROXY_TIMEOUT_SECONDS` | `300` | Max seconds to wait for agent response |

---

## MLflow Evaluation

Run a simulated multi-turn evaluation against 4 pre-defined test personas (freshie, placement seeker, culture explorer, struggling sophomore):

```bash
uv run agent-evaluate
```

This uses `mlflow.genai.evaluate` with `ConversationSimulator` and scores responses across:
`Completeness`, `ConversationCompleteness`, `ConversationalSafety`, `KnowledgeRetention`, `UserFrustration`, `Fluency`, `RelevanceToQuery`, `Safety`, `ToolCallCorrectness`.

Results are logged to your MLflow experiment.

---

## Example Questions

```
What do students think about hostel food at IITB?
What are the placement stats for CS students?
Which fests should a freshie attend?
How do people deal with academic pressure and avoid getting an FR?
What's the vibe like at YP and the Shack?
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| MCP tools not loading | Verify `VECTOR_SEARCH_INDEX` and `GENIE_SPACE_ID`; check that the VS endpoint and Genie space are active |
| Port already in use | `lsof -ti :8000 \| xargs kill -9` (or the relevant port) |
| Pre-flight fails with auth error | Re-run `databricks configure --token` or check `DATABRICKS_CONFIG_PROFILE` |
| `Tool not found` in logs | Tool names use `__` as separator: e.g., `iitb__bharat_bricks__vs_gold_posts_index` |
| Slow responses | Increase `CHAT_PROXY_TIMEOUT_SECONDS`; check Genie Space and VS endpoint health |
| Bundle deploy fails | Ensure resources (experiment, VS index, Genie space) exist before deploying |
| App won't start on Databricks | Check **Compute → Apps → iitb-baap-agent → Logs** for startup errors |

---

*Part of the [Bharat Bricks IITB Workshop](../README.md) — Step 11: Deploy Conversational Agent on Databricks Apps.*
