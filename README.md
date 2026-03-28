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
| ↳ `1-register-databricks-free-account.pdf` | Sign up for Databricks Free Edition |
| ↳ `2-catalog-data-setup.pdf` | Create catalog, schema, volume & upload data |
| ↳ `3-create-git-folder.pdf` | Connect GitHub repo to Databricks workspace |
| ↳ `4-ingest-data-maange-assets.pdf` | Data ingestion, permissions, security policies & quality monitoring |
| ↳ `5-creating-etl-pipelines.pdf` | UI-based ETL pipeline creation with AI Gateway & event logging |
| ↳ `6-create-dashboard.pdf` | Dashboard creation via Databricks UI with visualization widgets |
| ↳ `7-create-metric-view.pdf` | Creating metric views using Genie Code and UI navigation |
| ↳ `8-create-genie-space.pdf` | Deploy Genie Space via notebook with Genie Code assistance |
| ↳ `9-use-genie-space.pdf` | Query subreddit data using natural language in Genie |
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
> - [4-ingest-data-maange-assets.pdf](instructions/4-ingest-data-maange-assets.pdf) — Data ingestion, permissions, security policies & quality monitoring
> - [5-creating-etl-pipelines.pdf](instructions/5-creating-etl-pipelines.pdf) — UI-based ETL pipeline creation with AI Gateway & event logging
> - [6-create-dashboard.pdf](instructions/6-create-dashboard.pdf) — Dashboard creation via Databricks UI with visualization widgets
> - [7-create-metric-view.pdf](instructions/7-create-metric-view.pdf) — Creating metric views using Genie Code and UI navigation
> - [8-create-genie-space.pdf](instructions/8-create-genie-space.pdf) — Deploy Genie Space via notebook with Genie Code assistance
> - [9-use-genie-space.pdf](instructions/9-use-genie-space.pdf) — Query subreddit data using natural language in Genie

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

Upload the JSON files from `raw_data/` to your volume:
- `iitbombay_posts.json` → `/Volumes/iitb/bharat_bricks/data/`
- `iitbombay_comments.json` → `/Volumes/iitb/bharat_bricks/data/`

In Databricks: **Catalog → iitb → bharat_bricks → data → Upload to this volume**

**Step 4: Connect Git Repository** ([visual guide](instructions/3-create-git-folder.pdf))

**4.1: Generate GitHub Personal Access Token**
1. Go to GitHub.com and log in to your account
2. Navigate to **Settings → Developer settings → Personal access tokens → Tokens (classic)**
3. Click **Generate new token**
4. Set expiration and select **repo** scope (full repository access)
5. Copy the generated token (you won't see it again!)

**4.2: Add Git Credentials in Databricks**
1. In your Databricks workspace, click on your profile icon (top right)
2. Select **Settings → Linked accounts → Add Git credential**
3. Choose **Personal access token** as authentication method
4. Paste your GitHub token and save

**4.3: Create Git Folder**
1. Navigate to **Workspace → Create → Git folder**
2. Enter your repository URL in format: `https://github.com/username/bharatbricksiitb-git.git`
3. Click **Create Git folder**
4. Your repository files will now be accessible in the Databricks workspace

> **✅ Success Check**: After creating the Git folder, you should see your repository appear in **Workspace → Repos**. Click on it to access all project files and notebooks directly within Databricks.

**Step 5: Navigate to Your Git Folder**

After creating the Git folder, navigate to it in your Databricks workspace:
1. Go to **Workspace → Repos → bharatbricksiitb-git** (or your repository name)
2. You should see all project files and folders available
3. Click on notebooks to open them directly in Databricks

**Step 6: Configure Project Files**

```bash
# Update all project files to use your catalog
python setup.py --catalog iitb --schema bharat_bricks
```

> **Alternative**: You can also use the widget inputs at the top of each notebook to set your catalog and schema without running setup.py.

### Deploy Pipeline

**Option A: Notebook-Based Approach** (Recommended for learning)

Run notebooks in order (use the **widget inputs** at the top to set your catalog/schema):

**Step 7: Data Ingestion**

1. **`01-data-ingestion.ipynb`** — Auto Loader creates `posts` and `comments` tables

2. **`02-data-transformation/`** — Run SQL files in Databricks SQL Editor:
   - `silver_posts.sql`, `silver_comments.sql`
   - `gold_posts.sql`, `gold_comments.sql`
   - `gold_posts_chunked.sql` (optional, for agent)

3. **`03-metric-view.ipynb`** — Creates the metric view ([visual guide](instructions/7-create-metric-view.pdf))
   - Navigate to **Workspace → bharatbricksiitb → 03-metric-view**
   - Click the Genie Code icon and use prompt: `i want to use "iitb" catalog for creating this metric view`
   - Click **Accept all** and **run the cells**
   - When prompted, click **Always allow in current thread** for permissions
   - Click **Run** to execute the metric view creation
   - Verify creation by going to **Catalog → bharat_bricks → Tables(9) → iitb_subreddit_metrics**
   - Click on the metric view to explore its **Details** and structure

4. **Deploy dashboard**:
   ```bash
   python 04-deploy-dashboard.py
   ```

> **💡 Prefer UI?** See the **Alternative: UI-Based Pipeline Creation** and **Alternative: UI-Based Dashboard Creation** sections below for step-by-step visual workflows.

**Option B: UI-Based Approach** (Alternative workflow)

### Alternative: UI-Based Pipeline Creation

For those who prefer using the Databricks UI instead of notebooks ([visual guide](instructions/5-creating-etl-pipelines.pdf)):

**Step 1: Create ETL Pipeline via UI**

1. Navigate to **Workspace → Jobs & Pipelines**
2. Click **ETL pipeline**
3. Select **Associate this pipeline with code files already available in your Workspace**
4. Browse to your Git folder: **loading → bharatbricksiitb → 02-data-transformation**
5. Select transformation files and click **Add**

**Step 2: Configure Pipeline Settings**

1. Name your pipeline (e.g., "bharat-bricks-etl")
2. Click **Edit catalog and schema**:
   - **Catalog**: workspace → iitb
   - **Default schema**: bharat_bricks
3. Click **Save**

**Step 3: Configure AI Gateway (Optional)**

1. Add SQL files: `silver_posts.sql`, `silver_comments.sql`, `gold_posts.sql`, `gold_comments.sql`, `gold_posts_chunked.sql`
2. Navigate to **AI Gateway** tab
3. Search for "llama" and select `databricks-meta-llama-3-1-8b-instruct`
4. Copy the model name and paste into SQL files where needed

**Step 4: Configure Event Logging**

1. Click **Edit advanced settings**
2. Enable **Publish event log to Unity Catalog**
3. Set **Event log name**: `event_log_etl`
4. Select catalog: `iitb` and schema: `bharat_bricks`
5. Click **Save**

**Step 5: Run Pipeline**

1. Use **Dry run** first to test configuration
2. If errors occur, use **Genie Code** with prompt: "fix these errors"
3. Click **Run pipeline with full table refresh**
4. Monitor execution progress and metrics

### Alternative: UI-Based Dashboard Creation

Create dashboards using the Databricks UI instead of deployment scripts ([visual guide](instructions/6-create-dashboard.pdf)):

**Step 1: Explore Your Data**

1. Navigate to **Catalog → iitb → bharat_bricks → gold_posts**
2. Click **Sample Data** to preview your tables
3. Familiarize yourself with available columns and data

**Step 2: Create Dashboard**

1. Go to **Dashboards** and click **Create dashboard**
2. Click **Data → Add data source**
3. Select catalog: `iitb` → schema: `bharat_bricks`
4. Add tables: `gold_comments` and `gold_posts`
5. Click **Confirm**

**Step 3: Build Visualizations**

1. Add text widget with title: **# IIT Bombay Subreddit**
2. Create charts using data from `gold_posts`:
   - **Author analysis**: Select `author` and `score` fields
   - **Engagement metrics**: Add aggregations and filters
   - **User flair analysis**: Filter by `author_flair_text` (All, Alum, etc.)

**Step 4: AI-Powered Dashboard Enhancement**

1. Use the AI assistant prompt: "do in depth analysis of gold tables and metric view inside this schema - iitb.bharat_bricks and then create a dashboard exploring student's live..."
2. Click **Plan** to let AI suggest dashboard structure
3. Select **Always allow in current thread** for automated enhancements

**Step 5: Publish Dashboard**

1. Click **Publish** when satisfied with your dashboard
2. Choose data permission model:
   - **Shared cache**: All viewers use your permissions (better performance)
   - **Individual permissions**: Each viewer uses their own access rights
3. Set access permissions:
   - **Subject**: All workspace users
   - **Permission level**: Can View or Can Manage
4. Click **Add** and **View published**

**Step 6: Explore Dashboard Sections**

Your published dashboard should include sections like:
- **Content Analysis**: Post categorization and trends
- **Engagement**: User interaction metrics
- **Trending Topics**: Popular discussion themes

### Data Asset Management & Configuration

After deploying the pipeline, configure data access, security, and monitoring ([visual guide](instructions/4-ingest-data-maange-assets.pdf)):

**Step 1: Using Genie Code for Configuration**

1. Navigate to **Workspace → bharatbricksiitb → 01-data-ingestion**
2. Click **Genie Code** and use the prompt: `"i want to use "iitb" as catalog for all my work"`
3. Accept suggestions and run all cells to complete data ingestion

**Step 2: Explore Data in Catalog**

1. Go to **Catalog → iitb → bharat_bricks → Tables**
2. Click on `posts` table to explore structure
3. Use **Sample Data** tab to preview and run sample queries
4. Select **Serverless Starter Warehouse** for compute

**Step 3: Configure Table Permissions**

Set up access control for your data tables:

1. Navigate to **Details → Permissions** for your table
2. Click **Grant** and select **All account users**
3. Choose **ALL PRIVILEGES** for workshop purposes
4. Click **Confirm**

> **Production Note**: Use principle of least privilege in production environments.

**Step 4: Set Up Security Policies** 

Configure data governance and privacy controls:

1. Go to **Policies** tab and click **New policy**
2. Configure subjects:
   - **All account users** for general access
   - Specific users (e.g., `visheshh.arya87@gmail.com`) for admin access
3. Apply security controls:
   - **Hide table rows** — Filter sensitive data
   - **Filter by business hours** — Time-based access control
   - **Mask column data** — Apply data masking (e.g., phone numbers with asterisks)
   - **Redact email addresses** — Remove PII from non-admin views

**Step 5: Enable Data Quality Monitoring**

Set up automated data quality checks:

1. Navigate to **Quality** tab in your table
2. Click **Enable** to activate monitoring
3. Select **Configure for schema** to apply schema-wide
4. Click **Save** to persist settings
5. Use **View results** to see quality metrics

**Step 6: Data Lineage Tracking**

Monitor data flow and dependencies:

1. Go to **Lineage** tab in your table
2. Click **See lineage graph** to visualize data flow
3. Explore upstream sources and downstream consumers
4. Use lineage for impact analysis and debugging

### Deploy Genie Space

**Option A: Notebook with Genie Code** (Recommended — [visual guide](instructions/8-create-genie-space.pdf))

1. Navigate to **Workspace → bharatbricksiitb → 05-iitb-junta-analytics-genie → deploy**
2. Click the **Genie Code** icon and type: `let's find the warehouse id and create this genie space`
3. When prompted for permissions, click **Ask every time** → **Always allow**
4. Click **Accept** to apply Genie Code suggestions (it will find your warehouse automatically)
5. Click **Allow** when prompted to run cells
6. Continue clicking **Always allow in current thread** for subsequent permission dialogs
7. Click **Accept all** to apply all suggested changes
8. Once deployed, click **Open Genie Space: 05 IITB Junta Analytics** link in the output

**Exploring Your Genie Space:**

After deployment, explore the Genie Space configuration:
- **About** — Space name, owner, warehouse, and description
- **Data** — Connected tables (`gold_comments`, `gold_posts`, `iitb_subreddit_metrics`)
- **Instructions** — General instructions, joins, SQL expressions, and SQL queries
- **Benchmarks** — Example questions for evaluation
- **Monitoring** — Activity history, errors, and feedback

**Sharing Your Genie Space:**

1. Click **Share** in the top menu
2. In the sharing dialog, click the subject dropdown
3. Select **All workspace users**
4. Choose permission level: **Can View** (recommended) or **Can Manage**
5. Click **Add** to grant access

**Option B: Command Line**

```bash
cd 05-iitb-junta-analytics-genie

# Set warehouse ID (get from SQL Warehouses page in Databricks)
export TARGET_WAREHOUSE_ID="your_warehouse_id"

# Deploy (uses catalog/schema from setup.py)
python deploy.py
```

> **Note**: Free Edition includes a Starter SQL warehouse that works with Genie.

### Using Your Genie Space ([visual guide](instructions/9-use-genie-space.pdf))

Once deployed, use Genie to analyze subreddit data with natural language:

**Accessing Genie:**

1. Click **Genie** in the left sidebar
2. Select your **05 IITB Junta Analytics** space
3. Type questions in the "Ask your question..." field

**Example Questions to Try:**

| Question | What You'll Get |
|----------|-----------------|
| "Show monthly post trends for 2025" | Time series chart of posting activity by month |
| "What is the distribution of posts by flair for the year 2025?" | Bar chart showing post counts by category (Tech, Survey, Question, etc.) |
| "Find trends for posting activity by day of week and semester cycles" | Analysis of when students post most (weekdays vs weekends, by academic term) |
| "Who are the most active authors?" | Leaderboard of top contributors |
| "Show High Engagement Rate by Flair" | Which categories get the most interaction |

**Understanding Genie Responses:**

Genie provides:
- **Analysis summary** — Natural language interpretation of your question
- **Result table** — Raw data with sortable columns
- **Visualizations** — Auto-generated charts (click to expand)
- **Show code** — View the SQL query Genie generated
- **Follow-up suggestions** — Related questions to explore further

**Tips for Better Queries:**

- Be specific about time periods: "for 2025", "last 6 months", "by academic term"
- Ask about specific dimensions: "by flair", "by author", "by day of week"
- Request comparisons: "compare Autumn Semester vs Spring Semester"
- Ask for insights: "what can be driving it", "why is this happening"

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
| "Catalog not found" | Run `setup.py --catalog YOUR_CATALOG` to update project files |
| "Volume not found" | Create volume: `CREATE VOLUME iitb.bharat_bricks.data` |
| "Table not found" | Run notebooks in order: 01 → 02 → 03 |
| Genie "warehouse not found" | Get warehouse ID from **SQL Warehouses** page, set `TARGET_WAREHOUSE_ID` |
| Wrong catalog in notebook | Use the widget inputs at the top of the notebook to set your catalog |
| Genie Code not responding | Make sure you're in the correct workspace folder and try refreshing the page |
| Sample data not loading | Verify your warehouse is started: **Catalog → Table → Sample Data → Select compute** |
| Permission denied errors | Check table permissions: **Catalog → Table → Details → Permissions** |
| Security policy not applying | Ensure policy subjects are correctly configured and saved |
| Data quality checks failing | Review schema consistency and enable monitoring: **Table → Quality → Enable** |
| Lineage graph empty | Run a few queries first to populate lineage data, then refresh **Lineage** tab |
| Git authentication failed | Verify your GitHub Personal Access Token has `repo` scope and hasn't expired |
| "Repository not found" during Git folder creation | Check repository URL format: `https://github.com/username/repo-name.git` |
| Git folder creation hangs | Ensure repository is public or you have proper access permissions |
| Can't find Git folder after creation | Navigate to **Workspace → Repos → [your-repo-name]** or check recent items |
| Git sync issues | Use **Git → Pull** in your Git folder to sync latest changes from repository |
| Permission denied on Git operations | Ensure your Personal Access Token hasn't expired and has sufficient permissions |
| **Metric View Creation Issues** | |
| Genie Code not responding for metric view | Navigate to correct notebook path: **Workspace → bharatbricksiitb → 03-metric-view** |
| Metric view creation fails | Use exact Genie Code prompt: `i want to use "iitb" catalog for creating this metric view` |
| Permission dialogs not appearing | Click **Always allow in current thread** when prompted for cell execution permissions |
| Metric view not visible in catalog | After creation, navigate to **Catalog → bharat_bricks → Tables → iitb_subreddit_metrics** |
| **ETL Pipeline Issues** | |
| Pipeline creation fails | Ensure Git folder is properly connected and transformation files are accessible |
| "Associate with code files" option missing | Check that you're in the correct workspace and have Git folder set up |
| AI Gateway model not found | Verify workspace has access to Foundation Model APIs; try searching for "llama" |
| Event log creation fails | Ensure you have permissions to create tables in the specified catalog/schema |
| Pipeline run stalls | Check compute resources and try running individual SQL files first |
| Genie Code not fixing errors | Ensure you're in a compatible workspace folder and have proper model access |
| **Dashboard Creation Issues** | |
| Data source connection fails | Verify tables exist and you have SELECT permissions on the catalog/schema |
| Visualization widgets not loading | Check that your SQL warehouse is running and accessible |
| AI dashboard suggestions not working | Ensure you have access to AI/BI capabilities in your workspace tier |
| Publish button disabled | Verify all required fields are filled and visualizations are valid |
| Shared cache permissions error | Choose "Individual permissions" option instead of shared cache |
| Dashboard not visible after publishing | Check access permissions and ensure users are added to the dashboard |
| **Genie Space Deployment Issues** | |
| Genie Code not finding warehouse | Ensure you have at least one SQL warehouse in your workspace; check **SQL Warehouses** page |
| "GenieAPI object has no attribute" error | Genie Code will auto-fix this by using REST API directly; click **Accept** on suggested changes |
| Genie Space not accessible after deploy | Click the **Open Genie Space** link in notebook output or navigate to **Genie** in sidebar |
| Sharing dialog not showing users | Verify you have admin permissions; try searching for specific usernames or groups |
| Genie Space queries timing out | Check warehouse size and state; ensure it's running and not in STOPPED state |
| **Genie Query Issues** | |
| Genie returns "no data found" | Verify tables have data; check catalog/schema references in Genie Space configuration |
| Query results seem wrong | Click **Show code** to review generated SQL; refine your question with more specific terms |
| Visualizations not appearing | Try clicking on the chart area or refresh; some complex queries may only show tables |
| Follow-up questions not working | Start a new conversation thread; context may be lost after complex queries |
| Genie misinterprets question | Use terminology from your data (e.g., "Academic Term", "Flair") rather than generic terms |

## License

Workshop materials for Bharat Bricks @ IIT Bombay.

---

**Questions?** Open an issue or reach out during the workshop!
