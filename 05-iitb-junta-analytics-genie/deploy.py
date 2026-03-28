#!/usr/bin/env python3
"""
Deploy IITB Junta Analytics Genie Space to a Databricks workspace.

Environment Variables:
    TARGET_WAREHOUSE_ID (required): SQL warehouse ID in target workspace
    TARGET_CATALOG (optional): Target catalog name (default: dbdemos_vishesh)
    TARGET_SCHEMA (optional): Target schema name (default: bharat_bricks)
    DATABRICKS_HOST (optional): Target workspace URL (uses default auth if not set)

Usage:
    export TARGET_WAREHOUSE_ID="your_warehouse_id"
    export TARGET_CATALOG="your_catalog"
    export TARGET_SCHEMA="your_schema"
    python deploy.py
"""

import json
import os
import re
import sys
from pathlib import Path

from databricks.sdk import WorkspaceClient


def load_json_file(filepath: Path) -> dict:
    """Load and parse a JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


def replace_catalog_schema(content: str, source_catalog: str, source_schema: str,
                           target_catalog: str, target_schema: str) -> str:
    """Replace all catalog.schema references in content."""
    source_fqn = f"{source_catalog}.{source_schema}"
    target_fqn = f"{target_catalog}.{target_schema}"

    # Replace both dotted and backtick-quoted formats
    content = content.replace(source_fqn, target_fqn)
    content = content.replace(f"`{source_catalog}`.`{source_schema}`", f"`{target_catalog}`.`{target_schema}`")

    return content


def main():
    # Get configuration from environment
    warehouse_id = os.environ.get("TARGET_WAREHOUSE_ID")
    if not warehouse_id:
        print("ERROR: TARGET_WAREHOUSE_ID environment variable is required")
        print("\nUsage:")
        print("  export TARGET_WAREHOUSE_ID='your_warehouse_id'")
        print("  export TARGET_CATALOG='your_catalog'  # optional")
        print("  export TARGET_SCHEMA='your_schema'    # optional")
        print("  python deploy.py")
        sys.exit(1)

    # Source catalog/schema (hardcoded from export)
    source_catalog = "dbdemos_vishesh"
    source_schema = "bharat_bricks"

    # Target catalog/schema (from env or defaults)
    target_catalog = os.environ.get("TARGET_CATALOG", source_catalog)
    target_schema = os.environ.get("TARGET_SCHEMA", source_schema)

    # Load exported files
    script_dir = Path(__file__).parent
    metadata = load_json_file(script_dir / "space_metadata.json")
    serialized_space = load_json_file(script_dir / "serialized_space.json")

    print(f"Deploying Genie Space: {metadata['title']}")
    print(f"  Source: {source_catalog}.{source_schema}")
    print(f"  Target: {target_catalog}.{target_schema}")
    print(f"  Warehouse: {warehouse_id}")

    # Replace catalog/schema references in serialized_space
    serialized_str = json.dumps(serialized_space)
    serialized_str = replace_catalog_schema(
        serialized_str,
        source_catalog, source_schema,
        target_catalog, target_schema
    )

    # Initialize Databricks client (uses default auth from env/config)
    w = WorkspaceClient()
    print(f"\nConnected to: {w.config.host}")

    # Create the Genie Space
    print("\nCreating Genie Space...")
    try:
        space = w.genie.create_space(
            warehouse_id=warehouse_id,
            serialized_space=serialized_str,
            title=metadata["title"],
            description=metadata["description"],
        )

        print(f"\nGenie Space created successfully!")
        print(f"  Space ID: {space.space_id}")
        print(f"  URL: {w.config.host}/genie/rooms/{space.space_id}")

    except Exception as e:
        print(f"\nERROR creating Genie Space: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
