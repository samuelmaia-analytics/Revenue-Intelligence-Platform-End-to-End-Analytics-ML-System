CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id INTEGER PRIMARY KEY,
    signup_date DATE NOT NULL,
    signup_month VARCHAR(7),
    channel VARCHAR(50),
    segment VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    year INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    quarter INTEGER
);

CREATE TABLE IF NOT EXISTS fact_orders (
    order_id VARCHAR(30) PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    order_date DATE NOT NULL,
    order_value DECIMAL(12, 2) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

