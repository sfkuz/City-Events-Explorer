INSERT INTO sources (code, name, base_url, scraper_type, is_active)
VALUES (
    'trojmiasto', 
    'Trójmiasto.pl', 
    'https://imprezy.trojmiasto.pl/', 
    'static',
    true
)
ON CONFLICT (code) DO NOTHING;

INSERT INTO source_category_feeds (source_id, feed_url, is_active)
SELECT id, 'https://imprezy.trojmiasto.pl/', true
FROM sources WHERE code = 'trojmiasto'
AND NOT EXISTS (
    SELECT 1 FROM source_category_feeds 
    WHERE source_id = (SELECT id FROM sources WHERE code = 'trojmiasto') 
      AND feed_url = 'https://imprezy.trojmiasto.pl/'
);


INSERT INTO sources (code, name, base_url, scraper_type, is_active)
VALUES (
    'going', 
    'Going.pl', 
    'https://goingapp.pl/', 
    'api', 
    true
)
ON CONFLICT (code) DO NOTHING;

INSERT INTO source_category_feeds (source_id, feed_url, is_active)
SELECT id, 'https://goingapp.pl/wydarzenia', true
FROM sources WHERE code = 'going'
AND NOT EXISTS (
    SELECT 1 FROM source_category_feeds 
    WHERE source_id = (SELECT id FROM sources WHERE code = 'going') 
      AND feed_url = 'https://goingapp.pl/wydarzenia'
);