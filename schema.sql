CREATE TYPE auction_status AS ENUM ('active', 'closed', 'cancelled');

CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    is_banned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE items (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    channel_post_id BIGINT,
    status auction_status DEFAULT 'active',
    deadline TIMESTAMP WITH TIME ZONE NOT NULL,
    winner_user_id BIGINT REFERENCES users(user_id),
    winning_bid NUMERIC(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bids (
    bid_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES items(item_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    bid_amount NUMERIC(10, 2) NOT NULL CHECK (bid_amount > 0),
    bid_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bids_item_amount ON bids (item_id, bid_amount);
CREATE UNIQUE INDEX idx_unique_user_item_bid ON bids (item_id, user_id, bid_amount);
