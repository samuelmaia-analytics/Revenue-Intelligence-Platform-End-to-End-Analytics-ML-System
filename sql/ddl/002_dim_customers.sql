CREATE TABLE IF NOT EXISTS dim_customers (
    customer_key INTEGER,
    customer_id INTEGER PRIMARY KEY,
    signup_date DATE NOT NULL,
    signup_month VARCHAR(7),
    channel VARCHAR(50),
    segment VARCHAR(50),
    gender VARCHAR(20),
    age INTEGER,
    city VARCHAR(100),
    membership_type VARCHAR(50),
    satisfaction_level VARCHAR(50)
);
