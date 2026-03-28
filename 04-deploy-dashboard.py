#!/usr/bin/env python3
"""
Deploy the IITB Lakeview Dashboard to a Databricks workspace.

This script reads the exported dashboard JSON and creates the dashboard
via the Lakeview API.

Configuration:
    Run `python setup.py --catalog YOUR_CATALOG` first to update catalog references
    in the dashboard JSON file.

Usage:
    python 04-deploy-dashboard.py
"""

import json
import sys
from pathlib import Path

from databricks.sdk import WorkspaceClient


def main():
    script_dir = Path(__file__).parent
    dashboard_file = script_dir / "04-life-at-iit-bombay.lvdash.json"

    if not dashboard_file.exists():
        print(f"ERROR: Dashboard file not found: {dashboard_file}")
        sys.exit(1)

    print("IITB Dashboard Deployment")
    print("=========================")

    # Read dashboard JSON (catalog/schema already set by setup.py)
    dashboard_json = dashboard_file.read_text()
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
