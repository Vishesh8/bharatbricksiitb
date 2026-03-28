CREATE OR REFRESH STREAMING TABLE silver_comments (
  CONSTRAINT valid_comment_id EXPECT (comment_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT has_body EXPECT (body IS NOT NULL AND LENGTH(TRIM(body)) > 0) ON VIOLATION DROP ROW
)
TBLPROPERTIES('pipelines.channel' = 'PREVIEW')
AS
SELECT
  comment_id,
  post_id,
  parent_id,
  author,
  body,
  created_at,
  score,
  depth,
  is_submitter,
  edited,
  distinguished,
  permalink,
  gilded,
  total_awards_received,
  -- AI-based content moderation: classify comment body using GPT-5 nano
  CASE
    WHEN LENGTH(TRIM(COALESCE(body, ''))) > 3
    THEN LOWER(TRIM(ai_query(
      'databricks-gpt-5',
      CONCAT('Classify this text as exactly one of: clean, profanity, slur, discrimination, harassment, harmful. Output ONLY the label, nothing else.\nText: ', body)
    )))
    ELSE 'clean'
  END AS content_moderation_label
FROM STREAM(comments)
WHERE
  -- Rule-based: remove deleted authors
  author != '[deleted]'
  -- Rule-based: remove deleted/removed comment bodies
  AND body NOT IN ('[deleted]', '[removed]')
  AND body IS NOT NULL