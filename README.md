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
> - [4-data-ingestion.pdf](instructions/4-data-ingestion.pdf) — Run data ingestion notebooks using AI assistant

### Quick Start

**Step 1: Get a Databricks Workspace** ([visual guide](instructions/1-register-databricks-free-account.pdf))

If you don't have one, sign up for [Databricks Free Edition](https://www.databricks.com/try-databricks-free):
1. Search "databricks free edition" or visit the link above
2. Click "Get started free" and complete registration
3. Verify your email and log in

**Step 2: Create Catalog, Schema & Volume** ([visual guide](instructions/2-catalog-data-setup.pdf))

**2.1: Open SQL Editor**

1. In your Databricks workspace, click **SQL Editor** in the left sidebar
2. Click **SQL Query** to create a new query

**2.2: Create Catalog and Schema**

1. In the SQL Editor, paste the following commands:
   ```sql
   CREATE CATALOG IF NOT EXISTS iitb;
   CREATE SCHEMA IF NOT EXISTS iitb.bharat_bricks;
   ```
2. Highlight the SQL statements if needed
3. Click **Run selected** to execute the queries
4. Verify successful execution in the output panel

**2.3: Create Volume**

1. Navigate to **Catalog** in the left sidebar
2. Expand the catalog tree: click **iitb**
3. Click on **bharat_bricks** schema
4. Click the **Create** dropdown button (top right)
5. Select **Volume** from the menu
6. In the "Create a new volume" dialog:
   - **Volume name**: Enter `data`
   - **Volume type**: Select **Managed volume** (default, radio button selected)
   - **Choose catalog and schema**: Verify `iitb` and `bharat_bricks` are selected
7. Click **Create**

**Step 3: Upload Raw Data** ([visual guide](instructions/2-catalog-data-setup.pdf))

1. In the Catalog view, navigate to the volume you just created:
   - Expand: **Catalog → iitb → bharat_bricks → data**
2. Click on the **data** volume to open it
3. Click **Upload to this volume** button (top right)
4. In the "Upload files to a Volume in Unity Catalog" dialog:
   - Either drag and drop files from your local `raw_data/` folder into the drop zone, or
   - Click **browse** (or **Select files**) to choose files manually
5. Select both JSON files from the [`raw_data/`](raw_data/) folder:
   - `iitbombay_posts.json`
   - `iitbombay_comments.json`
6. Click **Upload** to start the upload process
7. Wait for the upload to complete — you should see both files listed in the volume with their file sizes

**Step 4: Connect Git Repository** ([visual guide](instructions/3-create-git-folder.pdf))

**4.1: Generate GitHub Personal Access Token**

1. Navigate to https://github.com/settings/tokens or:
   - Go to GitHub.com and log in
   - Click your profile icon (top right) → **Settings**
   - Select **Developer settings** from the left sidebar
2. Click **Personal access tokens** → **Tokens (classic)**
3. Click **Generate new token** dropdown → **Generate new token (classic)**
4. Fill in the token details:
   - **Note**: Enter a descriptive name (e.g., "databricks-workshop")
   - **Expiration**: Choose expiration period (30 days recommended)
   - **Scopes**: Select the following checkboxes:
     - ☑ **repo** (full control of private repositories)
     - ☑ **project** (full control of projects)
5. Scroll down and click **Generate token**
6. **Important**: Copy the generated token immediately — you won't be able to see it again!

**4.2: Add Git Credentials in Databricks**

1. In your Databricks workspace, click your profile icon (top right)
2. Select **Settings** from the dropdown menu
3. Navigate to **Linked accounts** in the left sidebar
4. Click **Add Git credential** button
5. In the "Add Git credential" dialog:
   - **Git provider**: Select **GitHub** from the dropdown
   - **Authentication method**: Click **Personal access token** radio button
   - **Nickname**: Will auto-populate (e.g., "GitHub 2026-04-10 14:03:09")
   - **Git provider email (optional)**: Enter your GitHub email address
   - **Token**: Paste the personal access token you copied earlier
6. Click **Save**

**4.3: Create Git Folder**

1. Navigate to **Workspace** in the left sidebar
2. Click the **Create** dropdown (or use the **+** button)
3. Select **Git folder** from the menu
4. In the "Create Git folder" dialog:
   - **Git repository URL**: Enter your repository URL
     - Format: `https://github.com/YOUR-USERNAME/bharatbricksiitb.git`
     - Example: `https://github.com/Vishesh8/bharatbricksiitb.git`
   - **Git provider**: GitHub (auto-selected)
   - **Git folder name**: Will auto-populate from repository name
5. Click **Create Git folder**
6. Your repository files will now be accessible in the Databricks workspace under the Git folder

**Step 5: Navigate to Your Git Folder**

After creating the Git folder, navigate to it in your Databricks workspace:
1. Go to **Workspace → bharatbricksiitb-git** (or your repository name)
2. You should see all project files and folders available
3. Click on notebooks to open them directly in Databricks

**Step 6: Run Data Ingestion Using AI Assistant** ([visual guide](instructions/4-data-ingestion.pdf))

Use Genie Code (AI assistant) to automatically run the data ingestion notebook for your catalog and schema.

**6.1: Open the Data Ingestion Notebook**

1. In your Databricks workspace, click **Workspace** in the left sidebar
2. Navigate to your Git folder: **bharatbricksiitb** (or your repository name)
3. Click on the **01-data-ingestion** notebook to open it
4. The notebook will display the data ingestion pipeline architecture and configuration

**6.2: Use AI Assistant to Run the Notebook**

1. Look for the **Genie Code** icon in the right sidebar of the notebook
2. Click the Genie Code icon to open the AI assistant panel
3. In the chat input field, type your request:
   ```
   i want to run this data ingestion notebook for my catalog (iitb) and schema (bharat_bricks)
   ```
4. Press **Enter** to send the request

**6.3: Grant Permissions**

1. Genie Code will analyze the notebook and prepare to execute it
2. A permission dialog will appear: **"Ask every time"** or **"Always allow in current thread"**
3. Click **Always allow in current thread** to streamline future requests
4. Review the proposed changes in the assistant panel
5. Click **Accept all** to proceed with notebook execution

**6.4: Monitor Execution and View Results**

The AI assistant will:
- Update the configuration cells with your catalog and schema names
- Execute all cells in the notebook sequentially
- Display progress and execution results

You'll see output similar to:
```
Data Ingested:
• 1,339 posts from r/iitbombay → iitb.bharat_bricks.posts
• 16,790 comments → iitb.bharat_bricks.comments
• Average of 12.5 comments per post

Pipeline Features Activated:
• Auto Loader configured for incremental JSON processing
• Primary keys and foreign key constraints established
• Change Data Feed enabled for downstream incremental reads
• Comprehensive table and column documentation added
```

**6.5: Verify Data in Catalog**

1. Navigate to **Catalog** in the left sidebar
2. Expand the catalog tree: **iitb → bharat_bricks → Tables (2)**
3. You should see two new tables:
   - **comments** — Reddit comment data with threading structure
   - **posts** — Reddit post submissions with metadata
4. Click on either table to view:
   - **Overview**: Table description and metadata
   - **Sample Data**: Preview rows (requires SQL warehouse)
   - **Details**: Schema, constraints, and column descriptions
   - **Permissions**: Access control settings

**6.6: Query Sample Data (Optional)**

To view sample data from the tables:
1. Click on a table (e.g., **comments** or **posts**)
2. Click the **Sample Data** tab
3. If prompted to **Select compute**:
   - Click **Select compute**
   - Choose **Serverless Starter Warehouse**
   - Click **Start and Close**
4. The warehouse will start, and sample data will load automatically
5. Explore the data structure and verify successful ingestion


---

**Questions?** Open an issue or reach out during the workshop!
