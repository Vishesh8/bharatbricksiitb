CREATE OR REFRESH MATERIALIZED VIEW gold_posts_chunked
COMMENT 'Chunked r/iitbombay posts with chronological comments for vector search. Chunks split at comment/paragraph boundaries, targeting ~4000 chars without truncating any comment.'
AS
WITH comments_agg AS (
  -- Aggregate comments per post in chronological order
  SELECT
    post_id,
    ARRAY_JOIN(
      TRANSFORM(
        ARRAY_SORT(
          COLLECT_LIST(
            named_struct('ts', created_at, 'text', CONCAT('[', author, ' | score: ', CAST(score AS STRING), '] ', body))
          )
        ),
        x -> x.text
      ),
      '\n\n'
    ) AS comments_text
  FROM gold_comments
  GROUP BY post_id
),
combined AS (
  -- Combine post content with aggregated comments into a single document
  SELECT
    p.post_id,
    p.title,
    p.author,
    p.created_at,
    p.flair,
    p.score,
    p.upvote_ratio,
    p.num_comments,
    p.content_type,
    p.permalink,
    CONCAT(
      p.title, '\n\n',
      COALESCE(p.body, ''), '\n\n',
      'Comments:\n\n',
      COALESCE(ca.comments_text, 'No comments yet.')
    ) AS full_text
  FROM gold_posts p
  LEFT JOIN comments_agg ca ON p.post_id = ca.post_id
),
chunked AS (
  -- Split full_text at paragraph/comment boundaries (\n\n), accumulating
  -- segments into chunks of ~4000 chars without truncating any segment
  SELECT
    c.*,
    AGGREGATE(
      SPLIT(c.full_text, '\n\n'),
      named_struct('chunks', FILTER(ARRAY(''), x -> FALSE), 'cur', ''),
      (acc, seg) ->
        IF(LENGTH(CONCAT(acc.cur, '\n\n', seg)) > 4000 AND acc.cur != '',
           named_struct('chunks', array_append(acc.chunks, acc.cur), 'cur', seg),
           named_struct('chunks', acc.chunks, 'cur',
             IF(acc.cur = '', seg, CONCAT(acc.cur, '\n\n', seg)))
        ),
      acc -> FILTER(array_append(acc.chunks, acc.cur), x -> LENGTH(x) > 0)
    ) AS chunks_array
  FROM combined c
)
-- Explode chunks into individual rows for vector search embedding
SELECT
  post_id,
  title,
  author,
  created_at,
  flair,
  score,
  upvote_ratio,
  num_comments,
  content_type,
  permalink,
  chunk_index,
  CONCAT(post_id, '_', CAST(chunk_index AS STRING)) AS chunk_id,
  chunk_text,
  LENGTH(chunk_text) AS chunk_text_length,
  SIZE(chunks_array) AS total_chunks
FROM chunked
LATERAL VIEW POSEXPLODE(chunks_array) t AS chunk_index, chunk_text