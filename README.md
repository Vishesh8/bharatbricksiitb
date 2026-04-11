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

**Step 7: Run Data Transformation Pipeline With AI-Powered Cleansing** ([visual guide](instructions/05-data-transformation.pdf))

Use Delta Live Tables (DLT) pipelines to transform raw data into silver and gold tables with AI-powered content moderation using Llama 3.1 8B for batch inferencing.

**7.1: Create ETL Pipeline**

1. In your Databricks workspace, click **Catalog** in the left sidebar (or navigate to **Jobs & Pipelines**)
2. Click **Jobs & Pipelines** in the left sidebar
3. Click **ETL pipeline** to create a new pipeline
4. In the "Give your pipeline a name" field, type: `02-data-transformation`

**7.2: Configure Pipeline Settings**

1. Click **workspace** dropdown to select the target location
2. Click **iitb** to select the catalog
3. Click **Select schema**
4. Click **bharat_bricks** to select the schema

**7.3: Add Transformation Assets**

1. Click **Add existing assets** under "Advanced options"
2. In the "Pipeline root folder" section, click **Browse**
3. Navigate to: **bharatbricksiitb → 02-data-transformation**
4. Click **Select** to confirm the folder
5. In the "Source code paths" section, click the folder icon
6. Click **transformations** folder
7. Click **Select** to add all transformation SQL files
8. Click **Add** to finalize the pipeline configuration

You should now see the pipeline with the following assets:
- `gold_comments.sql`
- `gold_posts.sql`
- `silver_comments.sql`
- `silver_posts.sql`

**7.4: Configure AI Model for Data Cleansing**

Use Genie Code to switch from GPT-5 to Llama 3.1 8B for content moderation (compatible with Free Edition):

1. Click **Genie Code** icon in the right sidebar
2. In the chat input field, type:
   ```
   i want to use llama 3.1 8b for batch inferencing for cleansing raw data instead of gpt-5 as gpt-5 may not be available in the free edition
   ```
3. Press **Enter** to send the request
4. When prompted for permissions:
   - Click **Always allow in current thread** to streamline execution
5. Review the proposed code changes in the assistant panel
6. Click **Accept all** to apply the changes

Genie Code will update the `silver_comments.sql` and `silver_posts.sql` files to use Llama 3.1 8B (`databricks-meta-llama-3-1-8b-instruct`) for AI-based content moderation.

**7.5: Run the Pipeline**

1. Click the **Run pipeline** dropdown (top right)
2. Select **Run pipeline with full table refresh**
3. In the confirmation dialog, click **Start full refresh**
4. The pipeline will execute and create four tables:
   - **silver_comments** — Cleansed comments with AI content moderation
   - **silver_posts** — Cleansed posts with AI content moderation
   - **gold_comments** — Final comment data (deleted/bot content removed)
   - **gold_posts** — Final post data with content classification

**7.6: Monitor Data Quality with Expectations**

Delta Live Tables provides built-in data quality monitoring through expectations:

1. Once the pipeline completes, navigate to the **Tables** tab at the bottom
2. Click on **gold_posts** to view table metrics
3. Click the **Expectations** count (e.g., "1 unmet")
4. Review the **Expectations** panel showing:
   - **Written**: Records that passed validation (e.g., 74.8% or 923 records)
   - **Dropped**: Records that failed validation (e.g., 25.2% or 311 records)
   - **Expectation details**: `is_clean_content` expectation with DROP action

The `is_clean_content` expectation uses Llama 3.1 8B to classify comment/post body content and drops records containing profanity, slurs, discrimination, harassment, or hateful content.

5. Click on **gold_comments** to view comment-level expectations
6. Review expectations showing:
   - **Written**: 61.4% (9,013 comments)
   - **Dropped**: 38.6% (5,678 comments)

**7.7: Verify Transformed Data**

Navigate to the Catalog to view the new gold tables:

1. Click **Catalog** in the left sidebar
2. Expand: **iitb → bharat_bricks → Tables**
3. You should now see 6 tables total:
   - **comments** — Raw Reddit comments
   - **posts** — Raw Reddit posts
   - **gold_comments** — Cleansed, high-quality comments
   - **gold_posts** — Cleansed, high-quality posts with content classification
   - **silver_comments** — Intermediate transformed comments
   - **silver_posts** — Intermediate transformed posts

**7.8: Explore Gold Tables**

1. Click on **gold_posts** table
2. Click **Sample Data** tab
3. Explore the new columns:
   - `post_id` — Unique Reddit post identifier (e.g., "1ab1cj1")
   - `title` — Post title
   - `body` — Optional text body of the Reddit post
   - All other metadata columns from the raw posts

4. Click on **gold_comments** table
5. Click **Sample Data** tab
6. Explore the cleansed comment data with deleted/bot content removed

**Step 8: Configure Data Quality And Security Policies** ([visual guide](instructions/06-unity-catalog.pdf))

> **Note**: This step is optional and for exploration purposes. Data classification features may not be available in Databricks Free Edition.

Implement Unity Catalog governance features including data quality monitoring, automated data classification, and security policies with column-level masking.

**8.1: Grant Table Permissions**

1. Navigate to **Catalog** in the left sidebar
2. Expand: **iitb → bharat_bricks → Tables**
3. Click on **gold_posts** table
4. Click the **Details** tab
5. Click the **Permissions** tab
6. Click the **Grant** button
7. In the "Grant on iitb.bharat_bricks.gold_posts" dialog:
   - **Principals**: Click the dropdown and select **All account users**
   - **Privileges**: Select **ALL PRIVILEGES** (grants ownership-like ability for the object)
8. Click **Confirm** to apply the permissions

**8.2: Explore Data Lineage**

1. Click the **Lineage** tab to view data lineage
2. Click **See lineage graph** to visualize the complete data flow
3. Explore the lineage graph showing:
   - **Upstream sources**: `silver_posts` (streaming table)
   - **Current table**: `gold_posts` (materialized view)
   - **Downstream consumers**: Dashboards, pipelines, genie spaces, and notebooks
4. Click on individual columns (e.g., **string**) to view column-level lineage
5. Use the graph to understand data dependencies and transformation pipelines

**8.3: Enable Data Quality Monitoring**

1. Click the **Insights** tab to view table insights
2. Click the **Quality** tab
3. Click **Enable** to activate Data Quality Monitoring
4. In the "Data Quality Monitoring" dialog:
   - Click **Configure for schema** to enable monitoring for all tables in the schema
5. Click **Save** to confirm

Unity Catalog will now:
- Automatically monitor freshness and completeness of all tables
- Use intelligent scanning to stay efficient and keep insights current
- Track table usage over the last 30 days
- Monitor frequent users, dashboards, notebooks, and queries

**8.4: AI-Generate Column Descriptions**

1. Navigate back to the **Details** tab
2. Scroll down to the **Description** section
3. Click **AI generate** button next to "Filter columns"
4. AI will automatically generate descriptions for all columns based on:
   - Column names and data types
   - Sample data and patterns
   - Table context and relationships
5. Review the generated descriptions for accuracy
6. Click **Save all** to apply all generated descriptions

Example generated descriptions:
- `comment_id`: Unique Reddit comment identifier (e.g., n61c7w1). Primary key.
- `post_id`: ID of the parent post this comment belongs to. Foreign key referencing posts.post_id.
- `parent_id`: Reddit thing ID of the parent (post or comment) (e.g. t3_1cawss)

**8.5: Create Data Masking Policies**

1. Click the **Policies** tab to view and create security policies
2. Click **New policy** to create a row-level or column masking policy
3. In the "New policy" dialog, configure the following:

**Purpose — Select masking type:**
- Select **Mask column data** (columns must have all selected tags to be masked)
- Deselect **Hide table rows** (restrict access to individual rows based on content)

**Conditions — Select masking function:**
- Click **Select existing** dropdown
- Choose **Serverless Starter Warehouse** (or your preferred compute)
- Under "Custom condition", click **Select function** to define masking behavior
- Example functions:
  - **Mask with asterisks**: Replace all characters with `*` (e.g., `john@example.com` → `****************`)
  - **Show first and last characters**: Show first 2 and last 4 characters (e.g., `1234-5678-9012-3456` → `12**-****-****-3456`)
  - **Redact email addresses**: Replace email with `***@***.***`

**Conditions — Select tag for masking:**
- Click the tag dropdown to select which columns should be masked
- Choose **class.us_bank_number** (tags columns containing US bank account numbers)
- Only columns with this specific tag will be masked

**General — Apply to principals:**
- **Applied to**: Click dropdown and select **All account users**
- **Except for**: Click dropdown and select specific users/groups to exempt (e.g., `user_9505fc852`)

4. Review the auto-generated policy code in the **Policy code (SQL)** panel
5. Click **Create** to activate the masking policy

**8.6: Enable Automated Data Classification**

1. Navigate to **Catalog** in the left sidebar
2. Click on the **iitb** catalog
3. Click the **Details** tab
4. Scroll down to the **Advanced** section
5. Locate **Data Classification** and click **Enable**

Unity Catalog will now:
- Automatically scan tables in the catalog and tag columns containing sensitive data
- Identify and classify PII (Personally Identifiable Information)
- Apply tags like `class.email`, `class.ssn`, `class.credit_card_number`, `class.us_bank_number`
- Enable automated policy enforcement based on classification tags

**8.7: Monitor Data Quality Results**

1. Navigate to **Catalog** in the left sidebar
2. Expand: **iitb → bharat_bricks**
3. Click on the **bharat_bricks** schema
4. Click the **Details** tab
5. Scroll down to **Advanced → Data Quality Monitoring**
6. Click **View results** to open the Data Quality Monitoring dashboard

The dashboard displays:
- **Data Quality**: Overall health score (e.g., 100% healthy)
- **Tables Monitored**: Number of tables being monitored (e.g., 7 tables)
- **All Monitored Tables**: Detailed view with columns:
  - **Schema**: Schema name (e.g., `bharat_bricks`)
  - **Table**: Table name (e.g., `gold_comments`, `gold_posts`)
  - **Status**: Training state (green dot = Training, yellow dot = Healthy, red dot = Error)
  - **Last Scanned**: Timestamp of most recent scan (e.g., "17 minutes ago")
  - **Impact**: Usage frequency (Low, Medium, High)
  - **Scan Frequency**: Monitoring cadence (e.g., "Every 1 week")
  - **Results**: Click **Review** to view detailed quality metrics

7. Click **Review** on any table to view:
   - Anomaly detection results
   - Freshness metrics (data recency)
   - Completeness metrics (null values, missing data)
   - Volume metrics (row counts over time)

**Step 9: Create Metric View for Analytics** ([visual guide](instructions/07-metric-view.pdf))

Create a unified metric view that consolidates r/iitbombay subreddit analytics with dimensions and measures for dashboards, AI/BI (Genie) spaces, and SQL queries.

**9.1: Open the Metric View Notebook**

1. In your Databricks workspace, click **Workspace** in the left sidebar
2. Navigate to your Git folder: **bharatbricksiitb** (or your repository name)
3. Click on the **03-metric-view** notebook to open it
4. The notebook will display the metric view configuration and SQL definition

**9.2: Use AI Assistant to Create the Metric View**

1. Look for the **Genie Code** icon in the right sidebar of the notebook
2. Click the Genie Code icon to open the AI assistant panel
3. In the chat input field, type your request:
   ```
   create this metric view for catalog "iitb" and schema "bharat_bricks"
   ```
4. Press **Enter** to send the request

**9.3: Grant Permissions**

1. Genie Code will analyze the notebook and prepare to execute it
2. A permission dialog will appear: **"Ask every time"** or **"Always allow in current thread"**
3. Click **Always allow in current thread** to streamline future requests
4. Review the proposed changes in the assistant panel
5. Click **Run** to execute the notebook cells
6. Click **Accept all** to proceed with metric view creation

**9.4: Verify Metric View Creation**

The AI assistant will:
- Update the configuration cells with your catalog and schema names
- Execute the SQL DDL to create the metric view
- Display success confirmation

You'll see output similar to:
```
Perfect! I've successfully created the metric view iitb.bharat_bricks.iitb_subreddit_metrics.

This metric view consolidates r/iitbombay subreddit analytics with:

Dimensions: Post date, month, year, academic term (semester), flair, content type, author, and author affiliation

Measures: Total posts, total comments, average post score, average comments per post, high engagement posts, high engagement rate, and unique authors
```

**9.5: Explore the Metric View in Catalog**

1. Navigate to **Catalog** in the left sidebar
2. Expand the catalog tree: **iitb → bharat_bricks → Tables**
3. Click on **iitb_subreddit_metrics** to open the metric view
4. Click the **Details** tab to view the metric view definition
5. Scroll down to see:
   - **Measures (7)**: Total Posts, Total Comments, Avg Post Score, Avg Comments per Post, High Engagement Posts, High Engagement Rate, Unique Authors
   - **Dimensions (8)**: Post Date, Post Month, Post Year, Academic Term, Flair, Content Type, Author, Author Affiliation

**9.6: View Data Lineage**

1. Click the **Lineage** tab to view upstream dependencies
2. Click **See lineage graph** to visualize the complete data flow
3. Explore the lineage graph showing:
   - **Upstream sources**: `gold_posts` and `gold_comments` (materialized views)
   - **Current metric view**: `iitb_subreddit_metrics` (metric view)
   - **Potential downstream consumers**: Dashboards, Genie spaces, notebooks, and SQL queries
4. The lineage graph shows how the metric view aggregates data from the cleansed gold tables

**Step 10: Create AI/BI Dashboard with Genie Code** ([visual guide](instructions/08-ai-bi-dashboards.pdf))

Use Genie Code to automatically create interactive dashboards that explore student life at IIT Bombay based on your gold tables and metric view.

**10.1: Navigate to Dashboards**

1. In your Databricks workspace, click **Dashboards** in the left sidebar
2. Click the **Create dashboard** button (or the **+** icon)
3. Select **Create dashboard** from the dropdown menu

**10.2: Create Dashboard with Genie Code**

1. In the new dashboard view, click the **Genie Code** icon in the right sidebar
2. In the Genie Code input box, type your request:
   ```
   do in depth analysis of gold tables and metric view inside this schema - iitb.bharat_bricks and then create a dashboard exploring student's lives at iit bombay
   ```
3. Press **Enter** to send the request

**10.3: Grant Permissions**

1. A permission dialog will appear: **"Ask every time"** or **"Always allow in current thread"**
2. Click **Always allow in current thread** to streamline dashboard creation
3. Genie Code will analyze the schema and create initial visualizations
4. When prompted again for permissions, click **Always allow in current thread**

**10.4: Refine Dashboard Organization**

Genie Code will create a comprehensive dashboard with multiple visualizations. To improve organization:

1. In the Genie Code input box, type:
   ```
   let's create different tabs for different sections

   also, there are a lot of untagged and unknown categories. let's filter those out
   ```
2. Press **Enter** and review the proposed changes
3. Next, type to improve layout:
   ```
   move heading markdowns to the top on all tabs
   ```
4. Press **Enter** to apply the changes

**10.5: Explore Dashboard Tabs**

The dashboard will be organized into multiple tabs, each focusing on different aspects of student life:

1. **Overview** — Dashboard summary with key metrics:
   - Total Posts, Total Comments, Active Community Members, High Engagement Rate
   - Student Activity Over Time (time series visualization)
   - Discussion Topics (by Flair) — bar chart showing topic distribution
   - Content Type Distribution — pie chart showing text posts vs. links/images/videos/galleries
   - Engagement Trends — line chart showing activity patterns

2. **Topics & Content** — Discussion topics analysis:
   - Posts by Year — bar chart showing posting trends over time
   - Discussion Topics (by Flair) — detailed breakdown of conversation topics
   - Content Type Distribution — visualization of content format preferences
   - High Engagement Posts by Topic — identifying which topics generate most discussion

3. **Community** — Student communities and engagement:
   - Engagement by Student Communities — bar chart showing participation by affiliation
   - Author Affiliation distribution
   - Community activity patterns and trends
   - Active contributors and community dynamics

4. **Popular Posts** — Most engaging content:
   - Table of most popular posts with titles, scores, and comment counts
   - Engagement by Student Communities — comparing post counts and average scores
   - High-engagement content analysis
   - Popular discussion threads

**10.6: Customize and Publish**

1. Click on any visualization to customize:
   - Edit queries, change chart types, adjust colors
   - Add filters to focus on specific time periods or topics
   - Modify axis labels and formatting
2. Click **Publish** (top right) to save and share the dashboard
3. Enter a dashboard name: `IIT Bombay Student Life Explorer` (or your preferred name)
4. Click **Publish** to make the dashboard available to your team

**Step 11: Deploy Analytics Genie Space for Natural Language Queries** ([visual guide](instructions/09-ai-bi-genie.pdf))

Use AI/BI Genie to create a conversational analytics interface that allows users to explore IIT Bombay student trends using natural language questions.

**11.1: Navigate to Genie Deployment Folder**

1. In your Databricks workspace, click **Workspace** in the left sidebar
2. Navigate to your Git folder: **bharatbricksiitb** (or your repository name)
3. Click on the **05-iitb-junta-analytics-genie** folder to open it
4. Click on the **deploy** notebook to open the deployment script

**11.2: Configure Genie Space Deployment**

1. In the deployment notebook, locate the configuration cells at the top
2. Click the **Run** button (or press **Shift+Enter**) to execute the first cell
3. In the **New Catalog** field, enter: `iitb`
4. In the **SQL Warehouse ID** field, you'll need to provide your warehouse ID

**11.3: Select SQL Warehouse**

1. Navigate to **SQL Warehouses** in the left sidebar
2. Click on **Serverless Starter Warehouse** (or your preferred warehouse)
3. Copy the warehouse ID from the URL or the details page
   - Format: `(ID: d3754c233dd0e522)` or similar
4. Return to the deployment notebook and paste the warehouse ID

**11.4: Run Deployment Notebook**

1. Click **Run all** (or manually run each cell sequentially)
2. The deployment script will:
   - Create widgets for parameterization
   - Validate required parameters (catalog, warehouse_id)
   - Deploy the exported Genie Space to your Databricks workspace
   - Configure the space with your catalog and schema settings
3. Wait for the deployment to complete — you should see a success message
4. Click the generated link to **Open Genie Space: 05 IITB Junta Analytics**

**11.5: Explore the Genie Space Interface**

Once the Genie Space opens, you'll see the analytics interface with several key sections:

1. **Data tab** — View and manage connected data sources:
   - Click **Data** to see available tables
   - Click **iitb.bharat_bricks** to view schema details
   - Tables: `gold_comments`, `gold_posts`, `iitb_subreddit_metrics` (metric view)

2. **Instructions tab** — Configure space behavior and context:
   - Click **Instructions** to view or edit guidance
   - **Text** — General instructions on how Genie should behave
   - **Joins** — Define relationships between tables
   - **SQL Expressions** — Create reusable measures and dimensions
   - **SQL Queries** — Pre-built queries that Genie can learn from

3. **Common questions** — Pre-configured sample queries:
   - "What topics are there and how are they connected? Give me a short summary."
   - "What is the monthly distribution of total posts in r/iitbombay?"

**11.6: Configure Instructions and Context**

**Instructions — Text:**

The Genie Space includes detailed instructions that guide the AI agent:

```
DATA CONTEXT:
This Genie space analyzes student life at IIT Bombay through the r/iitbombay subreddit:
- Posts span from April 2018 to March 2026 (~1,300 posts, ~17K comments)
- Posts are categorized by topic flair: Question, Acad, Tech, Cult, Sports, Mast, IIT Selection
- Affiliation Categories: Hostel, Department, Alumni, City/Region, Batch Year

ANALYTICS TERMINOLOGY:
- Engagement = comments + votes combined
- High engagement post = 2M+ comments OR 10M+ score
- OP = Original Poster, thread depth = how nested replies are
- Join posts and comments on post_id

QUERY GUIDANCE:
- For aggregated metrics use iitb_subreddit_metrics metric view with MEASURE()
- For text search use gold_posts, for comments use gold_comments
- Join posts and comments on post_id

RESPONSE STYLE — USE IITB LINGO:
Always try to respond using IIT Bombay campus slang wherever possible.
```

**Instructions — Joins:**

Pre-configured table joins for Genie to understand relationships:
- `iitb.bharat_bricks.gold_posts` ↔ `iitb.bharat_bricks.gold_comments` (on `post_id`)

**Instructions — SQL Expressions:**

You can add custom measures and dimensions:
1. Click **SQL Expressions** tab
2. Click **Add** → **Measure** to create aggregated metrics
3. Example measures:
   - Total Posts: `COUNT(post_id)`
   - Avg Score: `AVG(score)`
   - High Engagement Rate: `SUM(CASE WHEN is_high_engagement THEN 1 ELSE 0 END) / COUNT(*)`

**Instructions — SQL Queries:**

Pre-built queries that help Genie learn your data patterns:
1. Click **SQL Queries** tab to view saved queries
2. Example queries included:
   - "What are the top posts by engagement?"
   - "Show posting trends by academic term"
   - "What is the flair distribution?"
   - "Who are the most active authors?"

**11.7: Ask Natural Language Questions**

**Using Chat Mode:**

1. Click the **Ask your question...** field at the bottom
2. Type natural language queries, for example:
   ```
   What is the monthly distribution of total posts in r/iitbombay?
   ```
3. Press **Enter** to submit the query
4. Genie will analyze the request and generate:
   - SQL query to answer the question
   - Visualizations (charts, tables) showing results
   - Natural language summary of findings

**Using Agent Mode (Advanced Analysis):**

For more complex, multi-step analysis:

1. Click the **Agent** button (next to Chat)
2. Ask complex questions that require deeper reasoning:
   ```
   what are students talking about and why? are there any seasonal trends in the activity volume along with semester timelines?
   ```
3. Agent mode will:
   - Break down the question into multiple analytical steps
   - Generate multiple SQL queries to investigate different angles
   - Create visualizations showing topic distributions and activity trends
   - Provide comprehensive analysis with insights

**11.8: Example Analysis — Student Activity Trends**

Try this multi-part query to explore seasonal patterns:

**Query:**
```
what are students talking about and why? are there any seasonal trends in the activity volume along with semester timelines?
```

**Expected Results:**

Genie will generate a comprehensive analysis including:

1. **What Students Are Talking About:**
   - Discussion topics ranked by volume and engagement
   - Top categories: General Q&A (618 posts), Questions (174 posts), Cultural events, Politics (MACHAXX controversy)
   - Most engaging topics: Cultural Events & Campus Life, Questions, Academic discussions

2. **Why These Topics Drive Conversations:**
   - Cultural events (fest performances, hostel mess food, Holi celebrations) generate high engagement (0.8 rate, 276 comments)
   - Questions drive conversations through peer help and advice-seeking behavior
   - Academic discussions during placement season and end-of-year stress

3. **Activity Trends Over Time:**
   - Explosive growth starting December 2025 (192 posts) continuing through Spring 2026
   - March 2026 saw the highest activity (238 posts) — 10x jump from the 2024-25 academic year
   - Seasonal momentum among student junta during serious academic periods

4. **Semester-Specific Topic Shifts:**
   - **Autumn Semester:** General campus life (208 untagged posts)
   - **Spring Semester:** Questions (110 posts), Academic discussions (17 posts) on placement season stress

**11.9: Monitor Genie Performance**

Track conversation history and evaluate Genie's accuracy:

1. Click the **Monitor** tab to view recent questions and answers
2. Review the conversation history showing:
   - Question text
   - Type (Query, Request, etc.)
   - Rating (Good, Neutral, Poor)
   - User who asked
   - Timestamp

**11.10: Run Benchmarks (Optional)**

Test Genie's performance with pre-configured evaluation questions:

1. Click the **Benchmark** tab (next to Monitor)
2. Click **Questions (7)** to view benchmark questions
3. Review the test questions:
   - "How do posting trends and average post scores vary by academic term?"
   - "What are the top posts by combined engagement of score and comments?"
   - "What are the top topics discussed in the insti junta..."
   - "Which posts received low engagement this year..."

4. Click **Run all benchmarks** to execute the evaluation suite
5. Genie will run all benchmark questions and display:
   - Assessment: Good ✓ or needs improvement
   - Model output SQL queries
   - Ground truth SQL answers for comparison
   - Accuracy scores for each question

6. Review results to identify areas where Genie needs refinement

**11.11: Download Analysis Results**

Export insights for sharing or reporting:

1. After Genie generates an analysis, click **Download PDF** (if available)
2. The PDF will include:
   - Activity trends visualizations (line charts, bar charts)
   - Topic distribution analysis
   - Semester-specific insights
   - Natural language summary of findings

**11.12: Share the Genie Space**

Make the analytics interface available to your team:

1. Click the **Share** button (top right)
2. Configure access permissions:
   - **Can view:** Users can ask questions and view results
   - **Can edit:** Users can modify instructions and configure the space
3. Add individual users or groups
4. Click **Share** to grant access

**Step 12: Create Vector Search Index for Semantic Search** ([visual guide](instructions/10-vector-search.pdf))

Set up a vector search endpoint and index to enable advanced semantic search capabilities on your chunked post data. This allows you to perform similarity searches across IIT Bombay subreddit content using natural language queries.

**12.1: Create Vector Search Endpoint**

1. In your Databricks workspace, click **Compute** in the left sidebar
2. Click the **Vector Search** tab at the top
3. Click **Create endpoint** button (top right)
4. In the "Create endpoint" dialog:
   - **Name**: Enter `vs-iitb-bharat-bricks`
   - **Type**: Keep default (**Standard** - 20-50ms query latency, cheaper for smaller use cases)
   - Click **Advanced Settings** to review optional configurations:
     - **Serverless Usage Policy**: None (default)
     - **Min DPS Beta**: 0 (default)
5. Click **Confirm** to create the endpoint

The endpoint will provision and become available for serving vector search queries.

**12.2: Navigate to Vector Index Creation**

1. In your Databricks workspace, click **Workspace** in the left sidebar
2. Navigate to your Git folder: **bharatbricksiitb** (or your repository name)
3. Click on the **06-create-vector-index** folder to view the notebook
4. Open the notebook to view the vector index creation instructions (optional)

**12.3: Create Vector Search Index from Catalog**

1. Click **Catalog** in the left sidebar
2. Navigate to the catalog tree: **iitb → bharat_bricks → Tables**
3. Click on **gold_posts_chunked** table
   - This table contains chunked IIT Bombay posts with chronological comments for vector search
   - Chunks split at comment/paragraph boundaries, targeting ~4000 chars without truncating any comment
4. Click the **Create** dropdown button (top right)
5. Select **Vector search index** from the menu

**12.4: Configure Vector Search Index**

In the "Create vector search index" dialog, configure the following settings:

**Index structure:**

1. **Name**: Enter `vs_gold_posts_index`
2. **Primary key**: Click the dropdown and select **post_id**
3. **Columns to index**: Leave blank to index all columns (default)

**Index subtype:**

- Select **Hybrid Index** (combines keyword and vector search for better accuracy)
- Alternatively: **Full-Text Index** (Beta) for text-only search

**Embeddings:**

1. **Embedding source**: Select **Compute embeddings** (radio button)
2. **Embedding source column**: Click the dropdown and select **chunk_text**
   - This is the column containing the chunked post text to generate embeddings for
3. **Embedding model**: Click the dropdown and select **databricks-gte-large-en**
   - Databricks Foundation Model for high-quality text embeddings
4. **Sync computed embeddings**: Leave unchecked (default)

**Compute resources:**

1. **Vector Search endpoint**: Click the dropdown and select **vs-iitb-bharat-bricks Standard**
   - This is the endpoint you created in Step 12.1
2. **Sync mode**: Select **Triggered** (radio button)
   - Index updates are triggered manually or via API
   - Alternatively: **Continuous** for automatic incremental updates

**12.5: Review Advanced Settings and Create Index**

1. Click **Advanced settings** to expand optional configurations (optional):
   - **Budget policy**: None (default) - tag the index's costs for team or project budgeting
   - **Use a separate embedding model for queries**: Unchecked (default)
2. Review all configuration settings
3. Click **Create** to start index creation

**12.6: Monitor Index Creation Progress**

The vector search index will now be created:

1. Databricks will process the `gold_posts_chunked` table
2. Generate embeddings for each chunk using `databricks-gte-large-en` model
3. Create the vector index for similarity search
4. Add a computed column `__db_chunk_text_vector` containing the embeddings

You can monitor progress in the index overview page.

**12.7: Verify Vector Search Index**

Once the index creation completes:

1. Navigate to **Catalog** in the left sidebar
2. Expand: **iitb → bharat_bricks → Tables**
3. Click on **vs_gold_posts_index** to view the index details
4. Click the **Sample Data** tab to preview the indexed data
5. You should see a new column **__db_chunk_text_vector** containing vector embeddings

The vector search index is now ready for semantic search queries across IIT Bombay subreddit content.

**12.8: Test Vector Search (Optional)**

To test the vector search index using Python:

```python
from databricks.vector_search.client import VectorSearchClient

# Initialize vector search client
vsc = VectorSearchClient()

# Get the index
index = vsc.get_index(
    endpoint_name="vs-iitb-bharat-bricks",
    index_name="iitb.bharat_bricks.vs_gold_posts_index"
)

# Perform similarity search
results = index.similarity_search(
    query_text="What are students saying about placements?",
    columns=["post_id", "title", "chunk_text", "author"],
    num_results=5
)

# Display results
print(results)
```

This will return the top 5 most semantically similar chunks to your query, enabling natural language search across student discussions.

---

**Questions?** Open an issue or reach out during the workshop!
