CREATE OR REFRESH MATERIALIZED VIEW gold_posts (
  CONSTRAINT is_clean_content
    EXPECT (content_moderation_label = 'clean')
    ON VIOLATION DROP ROW
)
COMMENT 'Clean r/iitbombay posts — filtered for deleted users, NSFW, profanity, and slurs content. Ready for dashboards, Genie, and RAG.'
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
  spoiler,
  locked,
  domain,
  num_crossposts,
  subreddit_subscribers,
  content_type,
  image_urls,
  video_url,
  content_moderation_label
FROM silver_posts