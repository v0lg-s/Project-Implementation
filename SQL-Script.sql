-- ENUMs
CREATE TYPE user_role AS ENUM ('user', 'creator', 'admin', 'advertiser');
CREATE TYPE video_visibility AS ENUM ('public', 'private', 'followers_only');
CREATE TYPE currency_type AS ENUM ('USD', 'COP', 'EUR');
CREATE TYPE transaction_type AS ENUM ('subscription', 'gift', 'ad_payment');
CREATE TYPE subscription_status AS ENUM ('active', 'cancelled', 'expired');
CREATE TYPE report_status AS ENUM ('pending', 'resolved', 'rejected');

-- table app_user
CREATE TABLE app_user (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    last_name VARCHAR(100),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    profile_pic_url VARCHAR(255),
    role user_role NOT NULL,
    birth_date DATE
);

-- table video
CREATE TABLE video (
    video_id SERIAL PRIMARY KEY,
    creator_id INTEGER NOT NULL REFERENCES app_user(user_id) ON DELETE CASCADE,
    title VARCHAR(255),
    description TEXT,
    duration INTEGER,
    upload_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    visibility video_visibility DEFAULT 'public'
);

-- table follow
CREATE TABLE follow (
    id SERIAL PRIMARY KEY,
    follower_id INTEGER REFERENCES app_user(user_id) ON DELETE CASCADE,
    followed_id INTEGER REFERENCES app_user(user_id) ON DELETE CASCADE,
    follow_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- table subscriptionplan
CREATE TABLE subscriptionplan (
    plan_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    price INTEGER,
    duration_days INTEGER,
    description TEXT
);

-- table subscription
CREATE TABLE subscription (
    subscription_id SERIAL PRIMARY KEY,
    subscriber_id INTEGER REFERENCES app_user(user_id) ON DELETE CASCADE,
    creator_id INTEGER REFERENCES app_user(user_id) ON DELETE CASCADE,
    plan_id INTEGER REFERENCES subscriptionplan(plan_id),
    start_date DATE NOT NULL,
    end_date DATE,
    status subscription_status
);

-- table advertiser
CREATE TABLE advertiser (
    advertiser_id SERIAL PRIMARY KEY,
    company_name VARCHAR(100),
    billing_info TEXT
);

-- table campaign
CREATE TABLE campaign (
    campaign_id SERIAL PRIMARY KEY,
    advertiser_id INTEGER REFERENCES advertiser(advertiser_id),
    budget FLOAT,
    start_date DATE,
    end_date DATE,
    targeting_criteria TEXT
);

-- table transaction
CREATE TABLE transaction (
    transaction_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES app_user(user_id),
    advertiser_id INTEGER REFERENCES advertiser(advertiser_id),
    amount FLOAT NOT NULL,
    currency currency_type NOT NULL,
    type transaction_type NOT NULL,
    transaction_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status BOOLEAN DEFAULT TRUE
);

-- table virtualgift
CREATE TABLE virtualgift (
    gift_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    price FLOAT
);

-- table gifttransaction
CREATE TABLE gifttransaction (
    gift_tx_id SERIAL PRIMARY KEY,
    transaction_id INTEGER REFERENCES transaction(transaction_id),
    sender_id INTEGER REFERENCES app_user(user_id),
    receiver_id INTEGER REFERENCES app_user(user_id),
    gift_id INTEGER REFERENCES virtualgift(gift_id)
);

-- table contentreport
CREATE TABLE contentreport (
    report_id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES video(video_id) ON DELETE CASCADE,
    reporter_id INTEGER REFERENCES app_user(user_id),
    reviewed_by INTEGER REFERENCES app_user(user_id),
    reason TEXT,
    status report_status DEFAULT 'pending',
    report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
