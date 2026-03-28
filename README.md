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

- Databricks workspace with Unity Catalog
- SQL warehouse (Pro or Serverless for Genie)
- Python 3.11+ with `databricks-sdk`

### Deploy Pipeline

1. **Create catalog/schema**:
   ```sql
   CREATE CATALOG IF NOT EXISTS your_catalog;
   CREATE SCHEMA IF NOT EXISTS your_catalog.bharat_bricks;
   ```

2. **Upload raw data** to `/Volumes/your_catalog/bharat_bricks/data/`

3. **Run notebooks** in order:
   - `01-data-ingestion.ipynb` — creates posts/comments tables
   - `02-data-transformation/` — run SQL files via Databricks SQL
   - `03-metric-view.ipynb` — creates metric view

4. **Import dashboard**: Upload `04-life-at-iit-bombay.lvdash.json` via Dashboards UI

### Deploy Genie Space

```bash
cd 05-iitb-junta-analytics-genie

# Set target environment
export TARGET_WAREHOUSE_ID="your_warehouse_id"
export TARGET_CATALOG="your_catalog"
export TARGET_SCHEMA="bharat_bricks"

# Deploy
python deploy.py
```

### Deploy Agent

See [06-iitb-baap-agent/README.md](06-iitb-baap-agent/README.md) for agent setup with:
- Local development via `uv run start-app`
- Databricks Apps deployment via `databricks bundle deploy`

## Sample Queries

```sql
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

## License

Workshop materials for Bharat Bricks @ IIT Bombay.
