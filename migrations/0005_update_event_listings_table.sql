ALTER TABLE event_listings
ADD COLUMN canonical_event_id UUID REFERENCES events(id) ON DELETE SET NULL;