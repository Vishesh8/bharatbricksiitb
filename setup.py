#!/usr/bin/env python3
"""
Setup script to configure catalog and schema names across the project.

This script replaces hardcoded catalog/schema references in all project files,
allowing users to run the project with their own Databricks catalog.

Usage:
    python setup.py --catalog my_catalog
    python setup.py --catalog my_catalog --schema my_schema

    # Or use environment variables:
    export DATABRICKS_CATALOG="my_catalog"
    python setup.py
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# Default values (original hardcoded values)
DEFAULT_CATALOG = "dbdemos_vishesh"
DEFAULT_SCHEMA = "bharat_bricks"

# Files to update (relative to project root)
FILES_TO_UPDATE = [
    "01-data-ingestion.ipynb",
    "02-data-transformation/transformations/silver_posts.sql",
    "02-data-transformation/transformations/silver_comments.sql",
    "02-data-transformation/transformations/gold_posts.sql",
    "02-data-transformation/transformations/gold_comments.sql",
    "02-data-transformation/transformations/gold_posts_chunked.sql",
    "03-metric-view.ipynb",
    "04-life-at-iit-bombay.lvdash.json",
    "05-iitb-junta-analytics-genie/serialized_space.json",
    "05-iitb-junta-analytics-genie/space_metadata.json",
    "05-iitb-junta-analytics-genie/deploy.py",
    "06-iitb-baap-agent/agent_server/agent.py",
    "06-iitb-baap-agent/databricks.yml",
]


def replace_in_file(filepath: Path, old_catalog: str, new_catalog: str,
                    old_schema: str, new_schema: str) -> int:
    """Replace catalog and schema references in a file. Returns count of replacements."""
    if not filepath.exists():
        return 0

    content = filepath.read_text()
    original = content

    # Replace full qualified names: catalog.schema
    old_fqn = f"{old_catalog}.{old_schema}"
    new_fqn = f"{new_catalog}.{new_schema}"
    content = content.replace(old_fqn, new_fqn)

    # Replace backtick-quoted format: `catalog`.`schema`
    old_quoted = f"`{old_catalog}`.`{old_schema}`"
    new_quoted = f"`{new_catalog}`.`{new_schema}`"
    content = content.replace(old_quoted, new_quoted)

    # Replace volume paths: /Volumes/catalog/schema/
    old_volume = f"/Volumes/{old_catalog}/{old_schema}"
    new_volume = f"/Volumes/{new_catalog}/{new_schema}"
    content = content.replace(old_volume, new_volume)

    # Replace standalone catalog references (careful with this one)
    # Only in specific contexts like "source_catalog": "catalog_name"
    content = content.replace(f'"source_catalog": "{old_catalog}"',
                              f'"source_catalog": "{new_catalog}"')
    content = content.replace(f'source_catalog = "{old_catalog}"',
                              f'source_catalog = "{new_catalog}"')

    if content != original:
        filepath.write_text(content)
        # Count approximate replacements
        count = original.count(old_fqn) + original.count(old_quoted) + original.count(old_volume)
        return max(count, 1)
    return 0


def update_notebook_config(filepath: Path, new_catalog: str, new_schema: str) -> bool:
    """Update notebook to use environment variable pattern with new defaults."""
    if not filepath.exists():
        return False

    content = filepath.read_text()
    notebook = json.loads(content)

    # Find and update the config cell
    updated = False
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") == "code":
            source = "".join(cell.get("source", []))
            # Look for catalog assignment
            if 'catalog = ' in source and ('dbdemos_vishesh' in source or new_catalog in source):
                # Update to use env var pattern with new default
                new_source = f'''import os

# Configuration - override via environment variables or edit defaults below
catalog = os.environ.get("DATABRICKS_CATALOG", "{new_catalog}")
schema = os.environ.get("DATABRICKS_SCHEMA", "{new_schema}")
source_path = f"/Volumes/{{catalog}}/{{schema}}/data"
checkpoint_base = f"{{source_path}}/_checkpoints"

spark.sql(f"USE CATALOG {{catalog}}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {{schema}}")
spark.sql(f"USE SCHEMA {{schema}}")

print(f"Target: {{catalog}}.{{schema}}")
print(f"Source: {{source_path}}")
print(f"Checkpoints: {{checkpoint_base}}")'''
                cell["source"] = new_source.split("\n")
                cell["source"] = [line + "\n" for line in cell["source"][:-1]] + [cell["source"][-1]]
                updated = True
                break

    if updated:
        filepath.write_text(json.dumps(notebook, indent=2))
    return updated


def main():
    parser = argparse.ArgumentParser(
        description="Configure catalog and schema names for the IITB project"
    )
    parser.add_argument(
        "--catalog", "-c",
        default=os.environ.get("DATABRICKS_CATALOG", DEFAULT_CATALOG),
        help=f"Target catalog name (default: {DEFAULT_CATALOG} or DATABRICKS_CATALOG env var)"
    )
    parser.add_argument(
        "--schema", "-s",
        default=os.environ.get("DATABRICKS_SCHEMA", DEFAULT_SCHEMA),
        help=f"Target schema name (default: {DEFAULT_SCHEMA} or DATABRICKS_SCHEMA env var)"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent

    print(f"IITB Project Setup")
    print(f"==================")
    print(f"Source: {DEFAULT_CATALOG}.{DEFAULT_SCHEMA}")
    print(f"Target: {args.catalog}.{args.schema}")
    print()

    if args.catalog == DEFAULT_CATALOG and args.schema == DEFAULT_SCHEMA:
        print("No changes needed - using default catalog and schema.")
        print("\nTo configure for your workspace, run:")
        print(f"  python setup.py --catalog YOUR_CATALOG")
        return

    if args.dry_run:
        print("[DRY RUN] No files will be modified\n")

    total_changes = 0
    files_changed = 0

    for rel_path in FILES_TO_UPDATE:
        filepath = project_root / rel_path
        if not filepath.exists():
            print(f"  SKIP: {rel_path} (not found)")
            continue

        if args.dry_run:
            # Just check if file contains the old values
            content = filepath.read_text()
            if DEFAULT_CATALOG in content:
                print(f"  WOULD UPDATE: {rel_path}")
                files_changed += 1
        else:
            changes = replace_in_file(
                filepath,
                DEFAULT_CATALOG, args.catalog,
                DEFAULT_SCHEMA, args.schema
            )
            if changes > 0:
                print(f"  UPDATED: {rel_path} ({changes} replacements)")
                total_changes += changes
                files_changed += 1
            else:
                print(f"  OK: {rel_path} (no changes needed)")

    print()
    if args.dry_run:
        print(f"Would update {files_changed} files")
    else:
        print(f"Updated {files_changed} files ({total_changes} total replacements)")
        print()
        print("Next steps:")
        print("  1. Upload raw_data/*.json to /Volumes/{catalog}/{schema}/data/")
        print("  2. Run 01-data-ingestion.ipynb")
        print("  3. Run SQL files in 02-data-transformation/")
        print("  4. Run 03-metric-view.ipynb")
        print()
        print("Or set environment variable for runtime override:")
        print(f"  export DATABRICKS_CATALOG=\"{args.catalog}\"")


if __name__ == "__main__":
    main()
