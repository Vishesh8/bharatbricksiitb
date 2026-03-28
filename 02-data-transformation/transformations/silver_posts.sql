CREATE OR REFRESH STREAMING TABLE silver_posts (
  CONSTRAINT valid_post_id EXPECT (post_id IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT has_title EXPECT (title IS NOT NULL AND LENGTH(TRIM(title)) > 0) ON VIOLATION DROP ROW
)
TBLPROPERTIES('pipelines.channel' = 'PREVIEW')
AS
SELECT
  post_id,
  title,
  body,
  author,
  created_at,
  permalink,
  url,
  score,
  upvote_ratio,
  num_comments,
  flair,
  author_flair_text,
  is_self,
  is_video,
  is_original_content,
  is_nsfw,
  spoiler,
  locked,
  domain,
  num_crossposts,
  subreddit_subscribers,
  content_type,
  image_urls,
  video_url,
  -- AI-based content moderation: classify combined title+body using GPT-5 nano
  CASE
    WHEN LENGTH(TRIM(CONCAT(COALESCE(title, ''), ' ', COALESCE(body, '')))) > 3
    THEN LOWER(TRIM(ai_query(
      'databricks-gpt-5',
      CONCAT('Classify this text as exactly one of: clean, profanity, slur, discrimination, harassment, harmful. Output ONLY the label, nothing else.\nText: ', COALESCE(title, ''), ' ', COALESCE(body, ''))
    )))
    ELSE 'clean'
  END AS content_moderation_label
FROM STREAM(posts)
WHERE
  -- Rule-based: remove deleted authors
  author != '[deleted]'
  -- Rule-based: remove deleted/removed post bodies
  AND COALESCE(body, '') NOT IN ('[deleted]', '[removed]')
  -- Rule-based: remove NSFW-flagged posts
  AND is_nsfw = false