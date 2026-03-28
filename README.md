# Bharat Bricks — IITB Workshop

End-to-end data + AI pipeline analyzing the r/iitbombay subreddit — IIT Bombay campus life, academics, placements, hostel culture, and community discussions.

## Architecture

```
raw_data/               JSON files from Reddit API
    │
    ▼
01-data-ingestion       Auto Loader → bronze tables (posts, comments)
    │
    ▼
02-data-transformation  SQL transforms → silver → gold tables
    │
    ▼
03-metric-view          YAML metric view (iitb_subreddit_metrics)
    │
    ├───────────────────┬───────────────────┐
    ▼                   ▼                   ▼
04-dashboard        05-genie-space      06-agent
(Lakeview)          (AI/BI Chat)        (Responses API)
```

## Contents

| Path | Description |
|------|-------------|
| `instructions/` | **Start here!** Step-by-step PDF guides with screenshots |
| `raw_data/` | Source JSON files (~1,300 posts, ~17K comments) |
| `01-data-ingestion.ipynb` | Auto Loader pipeline → `posts` and `comments` tables |
| `02-data-transformation/` | SQL transforms: silver_posts, silver_comments, gold_posts, gold_comments |
| `03-metric-view.ipynb` | Creates `iitb_subreddit_metrics` metric view with 20+ measures |
| `04-life-at-iit-bombay.lvdash.json` | Lakeview dashboard (exportable) |
| `05-iitb-junta-analytics-genie/` | Genie Space export + deploy script |
| `06-iitb-baap-agent/` | Conversational agent (Responses API + Genie MCP) |

## Data Model

### Tables (Unity Catalog)

| Table | Description | Key |
|-------|-------------|-----|
| `posts` | Reddit submissions (title, body, score, flair) | `post_id` (PK) |
| `comments` | Comments with threading (body, score, depth) | `comment_id` (PK), `post_id` (FK) |
| `gold_posts` | Cleaned posts with content classification | `post_id` |
| `gold_comments` | Cleaned comments excluding deleted/bots | `comment_id` |

### Metric View

`iitb_subreddit_metrics` — unified analytics layer with:
- **Dimensions**: Post Date, Academic Term, Flair, Author, Affiliation, Content Type
- **Measures**: Total Posts, Avg Score, High Engagement Rate, Thread Depth, OP Engagement Rate

## Setup

### Prerequisites

- Databricks workspace with Unity Catalog (Free Edition works!)
- SQL warehouse (Pro or Serverless for Genie)
- Python 3.11+ with `databricks-sdk`

> **📖 Visual Guides**: See the `instructions/` folder for step-by-step screenshots:
> - [1-register-databricks-free-account.pdf](instructions/1-register-databricks-free-account.pdf) — Sign up for Databricks Free Edition
> - [2-catalog-data-setup.pdf](instructions/2-catalog-data-setup.pdf) — Create catalog, schema, volume & upload data

### Quick Start

**Step 1: Get a Databricks Workspace**

If you don't have one, sign up for [Databricks Free Edition](https://www.databricks.com/try-databricks-free):
1. Search "databricks free edition" or visit the link above
2. Click "Get started free" and complete registration
3. Verify your email and log in

See `instructions/1-register-databricks-free-account.pdf` for screenshots.

**Step 2: Create Catalog, Schema & Volume**

In Databricks, navigate to **Catalog** (left sidebar) and create:

```sql
-- Create your catalog (e.g., "iitb")
CREATE CATALOG IF NOT EXISTS iitb;

-- Create schema
CREATE SCHEMA IF NOT EXISTS iitb.bharat_bricks;

-- Create volume for raw data
CREATE VOLUME IF NOT EXISTS iitb.bharat_bricks.data;
```

See `instructions/2-catalog-data-setup.pdf` for the UI-based approach.

**Step 3: Upload Raw Data**

Upload the JSON files from `raw_data/` to your volume:
- `iitbombay_posts.json` → `/Volumes/iitb/bharat_bricks/data/`
- `iitbombay_comments.json` → `/Volumes/iitb/bharat_bricks/data/`

**Step 4: Configure Project Files**

```bash
# Update all project files to use your catalog
python setup.py --catalog iitb --schema bharat_bricks
```

**Alternative**: Use environment variables for runtime override:
```bash
export DATABRICKS_CATALOG="iitb"
export DATABRICKS_SCHEMA="bharat_bricks"
```

### Deploy Pipeline

Run notebooks in order:

1. **`01-data-ingestion.ipynb`** — Auto Loader creates `posts` and `comments` tables

2. **`02-data-transformation/`** — Run SQL files in Databricks SQL Editor:
   - `silver_posts.sql`, `silver_comments.sql`
   - `gold_posts.sql`, `gold_comments.sql`
   - `gold_posts_chunked.sql` (optional, for agent)

3. **`03-metric-view.ipynb`** — Creates the metric view

4. **Deploy dashboard**:
   ```bash
   python 04-deploy-dashboard.py
   ```

### Deploy Genie Space

```bash
cd 05-iitb-junta-analytics-genie

# Set target environment (get warehouse ID from SQL Warehouses page)
export TARGET_WAREHOUSE_ID="your_warehouse_id"
export TARGET_CATALOG="iitb"
export TARGET_SCHEMA="bharat_bricks"

# Deploy
python deploy.py
```

> **Note**: Free Edition includes a Starter SQL warehouse that works with Genie.

### Deploy Agent

See [06-iitb-baap-agent/README.md](06-iitb-baap-agent/README.md) for agent setup with:
- Local development via `uv run start-app`
- Databricks Apps deployment via `databricks bundle deploy`

## Sample Queries

Run these in the Databricks SQL Editor after setting your catalog context:

```sql
-- Set your catalog context first
USE CATALOG iitb;
USE SCHEMA bharat_bricks;

-- Top posts by engagement
SELECT title, author, flair, score, num_comments
FROM gold_posts
ORDER BY (score + num_comments) DESC
LIMIT 10;

-- Posting trends by academic term
SELECT `Academic Term`, MEASURE(`Total Posts`), MEASURE(`Avg Post Score`)
FROM iitb_subreddit_metrics
GROUP BY `Academic Term`;

-- Most active authors
SELECT author, COUNT(*) as posts, SUM(num_comments) as total_comments
FROM gold_posts
GROUP BY author
ORDER BY posts DESC
LIMIT 20;
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Catalog not found" | Run `setup.py --catalog YOUR_CATALOG` or set `DATABRICKS_CATALOG` env var |
| "Volume not found" | Create volume: `CREATE VOLUME iitb.bharat_bricks.data` |
| "Table not found" | Run notebooks in order: 01 → 02 → 03 |
| Genie "warehouse not found" | Get warehouse ID from **SQL Warehouses** page, set `TARGET_WAREHOUSE_ID` |

## License

Workshop materials for Bharat Bricks @ IIT Bombay.

---

**Questions?** Open an issue or reach out during the workshop!
