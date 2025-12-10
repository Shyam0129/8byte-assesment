"""
Airflow DAG for Stock Data Pipeline
Fetches AAPL stock data every 6 hours and stores in PostgreSQL
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys
import os

# Add scripts directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

# Import the fetch script
from fetch_stock_data import main as fetch_stock_main, verify_data_insertion

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 12, 10),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,  # Retry 3 times on failure
    'retry_delay': timedelta(minutes=5),  # Wait 5 minutes between retries
}

# Define the DAG
dag = DAG(
    'stock_data_pipeline',
    default_args=default_args,
    description='Fetch AAPL stock data from Alpha Vantage every 6 hours',
    schedule_interval='0 */6 * * *',  # Run every 6 hours (at 00:00, 06:00, 12:00, 18:00)
    catchup=False,  # Don't backfill past runs
    max_active_runs=1,  # Only one run at a time
    tags=['stock', 'alpha_vantage', 'aapl'],
)


def fetch_and_store_data(**context):
    """
    Task function to fetch and store stock data
    """
    try:
        # Call the main function from fetch_stock_data.py
        result = fetch_stock_main()
        
        if result:
            print("✅ Data fetching and storage completed successfully")
            return "success"
        else:
            print("❌ Data fetching and storage failed")
            raise Exception("Failed to fetch and store data")
            
    except Exception as e:
        print(f"❌ Error in fetch_and_store_data: {str(e)}")
        raise


def validate_data_insertion(**context):
    """
    Task function to validate that data was inserted correctly
    """
    try:
        stats = verify_data_insertion('AAPL')
        
        if stats['total_records'] > 0:
            print(f"✅ Data validation passed: {stats['total_records']} records found")
            print(f"   Latest data: {stats['latest_timestamp']}")
            return "validation_success"
        else:
            print("❌ Data validation failed: No records found")
            raise Exception("No data found in database")
            
    except Exception as e:
        print(f"❌ Error in validate_data_insertion: {str(e)}")
        raise


# Define tasks
task_fetch_store = PythonOperator(
    task_id='fetch_and_store_stock_data',
    python_callable=fetch_and_store_data,
    provide_context=True,
    dag=dag,
)

task_validate = PythonOperator(
    task_id='validate_data',
    python_callable=validate_data_insertion,
    provide_context=True,
    dag=dag,
)

# Task to log pipeline completion
task_log_completion = BashOperator(
    task_id='log_completion',
    bash_command='echo "Stock data pipeline completed at $(date)"',
    dag=dag,
)

# Define task dependencies
task_fetch_store >> task_validate >> task_log_completion
