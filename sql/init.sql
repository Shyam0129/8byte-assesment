-- Create stock_data table for storing AAPL stock market data
CREATE TABLE IF NOT EXISTS stock_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    close_price DECIMAL(10, 2),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_symbol ON stock_data(symbol);
CREATE INDEX IF NOT EXISTS idx_timestamp ON stock_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_symbol_timestamp ON stock_data(symbol, timestamp);

-- Grant permissions
GRANT ALL PRIVILEGES ON TABLE stock_data TO stockuser;
GRANT USAGE, SELECT ON SEQUENCE stock_data_id_seq TO stockuser;
