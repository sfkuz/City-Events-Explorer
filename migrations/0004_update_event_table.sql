DELETE FROM events
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY url ORDER BY created_at ASC) as rn
        FROM events
    ) sub
    WHERE rn > 1
);

ALTER TABLE events ADD CONSTRAINT events_url_unique UNIQUE (url);

ALTER TABLE events DROP COLUMN IF EXISTS description;
ALTER TABLE event_listings DROP COLUMN IF EXISTS description_html;
ALTER TABLE event_listings DROP COLUMN IF EXISTS description_text;