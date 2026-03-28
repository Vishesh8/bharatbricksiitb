#!/usr/bin/env python3
"""
Deploy IITB Junta Analytics Genie Space to a Databricks workspace.

Configuration:
    Run `python setup.py --catalog YOUR_CATALOG` from the project root first
    to update catalog references in serialized_space.json.

Environment Variables:
    TARGET_WAREHOUSE_ID (required): SQL warehouse ID in target workspace

Usage:
    export TARGET_WAREHOUSE_ID="your_warehouse_id"
    python deploy.py
"""

import json
import os
import sys
from pathlib import Path

from databricks.sdk import WorkspaceClient


def load_json_file(filepath: Path) -> dict:
    """Load and parse a JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


def main():
    # Get warehouse ID from environment (required, workspace-specific)
    warehouse_id = os.environ.get("TARGET_WAREHOUSE_ID")
    if not warehouse_id:
        print("ERROR: TARGET_WAREHOUSE_ID environment variable is required")
        print("\nUsage:")
        print("  export TARGET_WAREHOUSE_ID='your_warehouse_id'")
        print("  python deploy.py")
        print("\nNote: Run `python setup.py --catalog YOUR_CATALOG` from the project root")
        print("      first to configure your catalog/schema.")
        sys.exit(1)

    # Load exported files (catalog/schema already set by setup.py)
    script_dir = Path(__file__).parent
    metadata = load_json_file(script_dir / "space_metadata.json")
    serialized_space = load_json_file(script_dir / "serialized_space.json")

    print(f"Deploying Genie Space: {metadata['title']}")
    print(f"  Warehouse: {warehouse_id}")

    # Initialize Databricks client (uses default auth from env/config)
    w = WorkspaceClient()
    print(f"  Connected to: {w.config.host}")

    # Create the Genie Space
    print("\nCreating Genie Space...")
    try:
        space = w.genie.create_space(
            warehouse_id=warehouse_id,
            serialized_space=json.dumps(serialized_space),
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
