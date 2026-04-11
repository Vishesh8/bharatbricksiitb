"""
Centralized configuration for the IITB BAAP Agent.

All resource references are loaded from environment variables with sensible defaults.
To deploy to a new workspace, copy .env.example to .env and update the values.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# Catalog and Schema (base namespace for all resources)
# =============================================================================
CATALOG = os.getenv("DATABRICKS_CATALOG", "iitb")
SCHEMA = os.getenv("DATABRICKS_SCHEMA", "bharat_bricks")

# =============================================================================
# Genie Space Configuration
# =============================================================================
GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID", "01f135a25c7a1f63b039f802c37eaf5e")

# =============================================================================
# Vector Search Configuration
# =============================================================================
VECTOR_SEARCH_INDEX = os.getenv(
    "VECTOR_SEARCH_INDEX", f"{CATALOG}.{SCHEMA}.vs_gold_posts_index"
)

# =============================================================================
# Model Endpoint
# =============================================================================
MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT", "databricks-qwen3-next-80b-a3b-instruct")
