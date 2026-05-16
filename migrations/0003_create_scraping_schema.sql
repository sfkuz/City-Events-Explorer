CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    base_url TEXT NOT NULL,
    scraper_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS event_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS source_category_feeds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
    category_id UUID REFERENCES event_categories(id) ON DELETE CASCADE,
    feed_url TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_scraped_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS organizer_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
    source_organizer_id VARCHAR(255),
    source_organizer_name VARCHAR(255),
    source_organizer_url TEXT,
    UNIQUE(source_id, source_organizer_name)
);

CREATE TABLE IF NOT EXISTS event_listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
    organizer_profile_id UUID REFERENCES organizer_profiles(id) ON DELETE SET NULL,
    discovered_from_feed_id UUID REFERENCES source_category_feeds(id) ON DELETE SET NULL,

    external_event_id VARCHAR(255) NOT NULL,
    source_event_url TEXT NOT NULL,

    title VARCHAR(500) NOT NULL,
    description_text TEXT,
    description_html TEXT,
    event_start_at TIMESTAMP WITH TIME ZONE NOT NULL,
    event_end_at TIMESTAMP WITH TIME ZONE,
    city_text VARCHAR(255),
    location VARCHAR(255),
    genre VARCHAR(100),
    event_type VARCHAR(100),
    cover_image_url TEXT,
    price INT,
    price_currency VARCHAR(10) DEFAULT 'PLN',

    metadata_json JSONB DEFAULT '{}'::jsonb,
    raw_payload_json JSONB,
    raw_html TEXT,

    status VARCHAR(20) DEFAULT 'active',
    detail_status VARCHAR(20) DEFAULT 'pending',

    detail_attempts INT DEFAULT 0,
    detail_fetched_at TIMESTAMP WITH TIME ZONE,
    next_detail_retry_at TIMESTAMP WITH TIME ZONE,

    last_error TEXT,
    last_error_at TIMESTAMP WITH TIME ZONE,

    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(source_id, source_event_url)
);

CREATE INDEX idx_event_listings_details
ON event_listings (status, detail_status, next_detail_retry_at)
WHERE status = 'active' AND detail_status IN ('pending', 'failed');