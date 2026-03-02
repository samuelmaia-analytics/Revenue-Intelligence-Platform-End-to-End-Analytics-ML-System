CREATE TABLE IF NOT EXISTS fact_orders (
    order_id VARCHAR(30) PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    channel_key INTEGER,
    date_key INTEGER NOT NULL,
    order_date DATE NOT NULL,
    order_value DECIMAL(12, 2) NOT NULL,
    order_amount DECIMAL(12, 2) NOT NULL,
    order_count INTEGER NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (channel_key) REFERENCES dim_channel(channel_key)
);
