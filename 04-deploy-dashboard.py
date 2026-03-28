#!/usr/bin/env python3
"""
Deploy the IITB Lakeview Dashboard to a Databricks workspace.

This script reads the exported dashboard JSON, replaces catalog/schema references,
and creates/updates the dashboard via the Lakeview API.

Environment Variables:
    DATABRICKS_CATALOG: Target catalog name (default: dbdemos_vishesh)
    DATABRICKS_SCHEMA: Target schema name (default: bharat_bricks)

Usage:
    python 04-deploy-dashboard.py

    # Or with explicit catalog:
    DATABRICKS_CATALOG=my_catalog python 04-deploy-dashboard.py
"""

import json
import os
import sys
from pathlib import Path

from databricks.sdk import WorkspaceClient


# Default values (original hardcoded values)
DEFAULT_CATALOG = "dbdemos_vishesh"
DEFAULT_SCHEMA = "bharat_bricks"


def replace_catalog_schema(content: str, old_catalog: str, new_catalog: str,
                           old_schema: str, new_schema: str) -> str:
    """Replace catalog and schema references in content."""
    old_fqn = f"{old_catalog}.{old_schema}"
    new_fqn = f"{new_catalog}.{new_schema}"

    content = content.replace(old_fqn, new_fqn)
    content = content.replace(f"`{old_catalog}`.`{old_schema}`", f"`{new_catalog}`.`{new_schema}`")

    return content


def main():
    # Get configuration from environment
    target_catalog = os.environ.get("DATABRICKS_CATALOG", DEFAULT_CATALOG)
    target_schema = os.environ.get("DATABRICKS_SCHEMA", DEFAULT_SCHEMA)

    script_dir = Path(__file__).parent
    dashboard_file = script_dir / "04-life-at-iit-bombay.lvdash.json"

    if not dashboard_file.exists():
        print(f"ERROR: Dashboard file not found: {dashboard_file}")
        sys.exit(1)

    print("IITB Dashboard Deployment")
    print("=========================")
    print(f"Source: {DEFAULT_CATALOG}.{DEFAULT_SCHEMA}")
    print(f"Target: {target_catalog}.{target_schema}")
    print()

    # Read and transform dashboard JSON
    dashboard_json = dashboard_file.read_text()

    if target_catalog != DEFAULT_CATALOG or target_schema != DEFAULT_SCHEMA:
        dashboard_json = replace_catalog_schema(
            dashboard_json,
            DEFAULT_CATALOG, target_catalog,
            DEFAULT_SCHEMA, target_schema
        )
        print(f"Replaced catalog/schema references")

    dashboard_def = json.loads(dashboard_json)

    # Initialize Databricks client
    w = WorkspaceClient()
    print(f"Connected to: {w.config.host}")

    # Get current user for parent path
    current_user = w.current_user.me()
    parent_path = f"/Users/{current_user.user_name}"

    dashboard_name = "Life at IIT Bombay - r/iitbombay Analytics"

    print(f"\nCreating dashboard: {dashboard_name}")
    print(f"Parent path: {parent_path}")

    try:
        # Create the dashboard using Lakeview API
        dashboard = w.lakeview.create(
            display_name=dashboard_name,
            parent_path=parent_path,
            serialized_dashboard=json.dumps(dashboard_def),
        )

        print(f"\nDashboard created successfully!")
        print(f"  Dashboard ID: {dashboard.dashboard_id}")
        print(f"  URL: {w.config.host}/dashboardsv3/{dashboard.dashboard_id}")

    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"\nDashboard already exists. To update, delete the existing one first.")
            print(f"  Path: {parent_path}/{dashboard_name}")
        else:
            print(f"\nERROR creating dashboard: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
