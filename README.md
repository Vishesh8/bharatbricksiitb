# Bharat Bricks — IITB Workshop

End-to-end data + AI pipeline analyzing the r/iitbombay subreddit — IIT Bombay campus life, academics, placements, hostel culture, and community discussions.

## Architecture

<img width="2709" height="1944" alt="image" src="https://github.com/user-attachments/assets/ff6213c5-ba7e-41c2-a248-194406fe76bb" />

## Contents

| Path | Description |
|------|-------------|
| `instructions/` | **Start here!** Step-by-step PDF guides with screenshots |
| ↳ `1-register-databricks-free-account.pdf` | Sign up for Databricks Free Edition |
| ↳ `2-catalog-data-setup.pdf` | Create catalog, schema, volume & upload data |
| ↳ `3-create-git-folder.pdf` | Connect GitHub repo to Databricks workspace |
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

- **Databricks workspace** with Unity Catalog (Free Edition works!)
- **GitHub account** with access to fork/clone this repository
- **GitHub Personal Access Token** (classic) with `repo` scope for Git integration
- **SQL warehouse** (Pro or Serverless for Genie) — Free Edition includes Starter warehouse
- **Python 3.11+** with `databricks-sdk` (for local agent development only)

> **📖 Visual Guides**: See the `instructions/` folder for step-by-step screenshots:
> - [1-register-databricks-free-account.pdf](instructions/1-register-databricks-free-account.pdf) — Sign up for Databricks Free Edition
> - [2-catalog-data-setup.pdf](instructions/2-catalog-data-setup.pdf) — Create catalog, schema, volume & upload data
> - [3-create-git-folder.pdf](instructions/3-create-git-folder.pdf) — Connect GitHub repo to Databricks workspace

### Quick Start

**Step 1: Get a Databricks Workspace** ([visual guide](instructions/1-register-databricks-free-account.pdf))

If you don't have one, sign up for [Databricks Free Edition](https://www.databricks.com/try-databricks-free):
1. Search "databricks free edition" or visit the link above
2. Click "Get started free" and complete registration
3. Verify your email and log in

**Step 2: Create Catalog, Schema & Volume** ([visual guide](instructions/2-catalog-data-setup.pdf))

In Databricks SQL Editor, run:

```sql
CREATE CATALOG IF NOT EXISTS iitb;
CREATE SCHEMA IF NOT EXISTS iitb.bharat_bricks;
```

Then create a volume via Catalog UI: **Catalog → iitb → bharat_bricks → Create → Volume** (name it `data`).

**Step 3: Upload Raw Data** ([visual guide](instructions/2-catalog-data-setup.pdf))

Upload the JSON files from [`raw_data/`](raw_data/) to your volume:
- `iitbombay_posts.json` → `/Volumes/iitb/bharat_bricks/data/`
- `iitbombay_comments.json` → `/Volumes/iitb/bharat_bricks/data/`

In Databricks: **Catalog → iitb → bharat_bricks → data → Upload to this volume**

**Step 4: Connect Git Repository** ([visual guide](instructions/3-create-git-folder.pdf))

**4.1: Generate GitHub Personal Access Token**
1. Go to GitHub.com and log in to your account
2. Navigate to **Settings → Developer settings → Personal access tokens → Tokens (classic)**
3. Click **Generate new token**
4. Set expiration and select all on **repo** and **project** scope (full repository access)
5. Copy the generated token (you won't see it again!)

Alternatively, you can also do below:

**4.2: Add Git Credentials in Databricks**
1. In your Databricks workspace, click on your profile icon (top right)
2. Select **Settings → Linked accounts → Add Git credential**
3. Choose **Personal access token** as authentication method
4. Paste your GitHub token and save

**4.3: Create Git Folder**
1. Navigate to **Workspace → Create → Git folder**
2. Enter your repository URL in format: [`https://github.com/Vishesh8/bharatbricksiitb-git.git`](https://github.com/Vishesh8/bharatbricksiitb)
3. Click **Create Git folder**
4. Your repository files will now be accessible in the Databricks workspace

**Step 5: Navigate to Your Git Folder**

After creating the Git folder, navigate to it in your Databricks workspace:
1. Go to **Workspace → bharatbricksiitb-git** (or your repository name)
2. You should see all project files and folders available
3. Click on notebooks to open them directly in Databricks


---

**Questions?** Open an issue or reach out during the workshop!
