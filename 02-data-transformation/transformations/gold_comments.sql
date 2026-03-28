CREATE OR REFRESH MATERIALIZED VIEW gold_comments (
  CONSTRAINT is_clean_content
    EXPECT (content_moderation_label = 'clean')
    ON VIOLATION DROP ROW
)
COMMENT 'Clean r/iitbombay comments — filtered for deleted users, removed content, profanity, and slurs language. Ready for dashboards, Genie, and RAG.'
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
  content_moderation_label
FROM silver_comments