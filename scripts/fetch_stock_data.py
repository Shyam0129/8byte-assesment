"""
Stock Data Fetching Script
Fetches AAPL stock data from Alpha Vantage API and stores in PostgreSQL
"""

import os
import sys
import requests
import psycopg2
from datetime import datetime
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """
    Establishes and returns a PostgreSQL database connection
    
    Returns:
        psycopg2.connection: Database connection object
    
    Raises:
        Exception: If connection fails
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres_stock'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'stock_database'),
            user=os.getenv('POSTGRES_USER', 'stockuser'),
            password=os.getenv('POSTGRES_PASSWORD', 'stockpass123')
        )
        logger.info("Successfully connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise


def fetch_stock_data(symbol='AAPL'):
    """
    Fetches intraday stock data from Alpha Vantage API
    
    Args:
        symbol (str): Stock symbol to fetch (default: AAPL)
    
    Returns:
        dict: Parsed JSON response from API
    
    Raises:
        Exception: If API call fails
    """
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not api_key or api_key == 'your_api_key_here':
        logger.error("Alpha Vantage API key not configured")
        raise ValueError("API key not set. Please configure ALPHA_VANTAGE_API_KEY in .env file")
    
    # Alpha Vantage API endpoint for intraday data
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': symbol,
        'interval': '60min',  # Hourly data
        'apikey': api_key,
        'outputsize': 'compact'  # Returns latest 100 data points
    }
    
    try:
        logger.info(f"Fetching stock data for {symbol} from Alpha Vantage API...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            logger.error(f"API Error: {data['Error Message']}")
            raise ValueError(f"API Error: {data['Error Message']}")
        
        if 'Note' in data:
            logger.warning(f"API Note: {data['Note']}")
            raise ValueError(f"API rate limit reached: {data['Note']}")
        
        if 'Time Series (60min)' not in data:
            logger.error(f"Unexpected API response format: {list(data.keys())}")
            raise ValueError("Invalid API response format")
        
        logger.info(f"Successfully fetched data for {symbol}")
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while fetching data: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error fetching stock data: {str(e)}")
        raise


def parse_and_store_data(data, symbol='AAPL'):
    """
    Parses API response and stores data in PostgreSQL
    
    Args:
        data (dict): JSON response from Alpha Vantage API
        symbol (str): Stock symbol
    
    Returns:
        int: Number of records inserted/updated
    """
    conn = None
    cursor = None
    records_processed = 0
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        time_series = data.get('Time Series (60min)', {})
        
        if not time_series:
            logger.warning("No time series data found in API response")
            return 0
        
        logger.info(f"Processing {len(time_series)} data points...")
        
        # Prepare insert query with UPSERT logic (ON CONFLICT)
        insert_query = """
            INSERT INTO stock_data 
            (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol, timestamp) 
            DO UPDATE SET
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                volume = EXCLUDED.volume,
                created_at = CURRENT_TIMESTAMP
        """
        
        for timestamp_str, values in time_series.items():
            try:
                # Parse timestamp
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                # Extract values with error handling for missing data
                open_price = float(values.get('1. open', 0))
                high_price = float(values.get('2. high', 0))
                low_price = float(values.get('3. low', 0))
                close_price = float(values.get('4. close', 0))
                volume = int(values.get('5. volume', 0))
                
                # Insert/update record
                cursor.execute(insert_query, (
                    symbol,
                    timestamp,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume
                ))
                
                records_processed += 1
                
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping record {timestamp_str} due to parsing error: {str(e)}")
                continue
        
        # Commit the transaction
        conn.commit()
        logger.info(f"Successfully processed and stored {records_processed} records")
        
        return records_processed
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error storing data in database: {str(e)}")
        raise
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            logger.info("Database connection closed")


def verify_data_insertion(symbol='AAPL'):
    """
    Verifies that data was successfully inserted into the database
    
    Args:
        symbol (str): Stock symbol to verify
    
    Returns:
        dict: Summary statistics of stored data
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get count and latest timestamp
        cursor.execute("""
            SELECT COUNT(*), MAX(timestamp), MIN(timestamp)
            FROM stock_data
            WHERE symbol = %s
        """, (symbol,))
        
        count, max_timestamp, min_timestamp = cursor.fetchone()
        
        stats = {
            'total_records': count,
            'latest_timestamp': max_timestamp,
            'earliest_timestamp': min_timestamp
        }
        
        logger.info(f"Data verification: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error verifying data: {str(e)}")
        raise
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def main():
    """
    Main execution function
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting Stock Data Pipeline")
        logger.info("=" * 60)
        
        symbol = 'AAPL'
        
        # Step 1: Fetch data from API
        data = fetch_stock_data(symbol)
        
        # Step 2: Parse and store data
        records_count = parse_and_store_data(data, symbol)
        
        # Step 3: Verify insertion
        stats = verify_data_insertion(symbol)
        
        logger.info("=" * 60)
        logger.info(f"Pipeline completed successfully!")
        logger.info(f"Records processed: {records_count}")
        logger.info(f"Total records in database: {stats['total_records']}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Pipeline failed: {str(e)}")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
