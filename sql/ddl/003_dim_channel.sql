CREATE TABLE IF NOT EXISTS dim_channel (
    channel_key INTEGER PRIMARY KEY,
    channel VARCHAR(50) UNIQUE,
    acquired_customers INTEGER
);
