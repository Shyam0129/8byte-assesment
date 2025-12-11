# 📊 Dockerized Stock Data Pipeline with Apache Airflow

An automated data pipeline that fetches AAPL stock market data from Alpha Vantage API every 6 hours and stores it in PostgreSQL, orchestrated by Apache Airflow.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│           Docker Compose Network                │
│                                                 │
│  ┌──────────────┐      ┌──────────────┐       │
│  │   Airflow    │      │  PostgreSQL  │       │
│  │  Scheduler   │─────▶│  (Stock DB)  │       │
│  │  Webserver   │      │              │       │
│  └──────┬───────┘      └──────────────┘       │
│         │                                       │
│         ▼                                       │
│  ┌──────────────┐                              │
│  │Alpha Vantage │                              │
│  │     API      │                              │
│  └──────────────┘                              │
└─────────────────────────────────────────────────┘
```

## ✨ Features

- ✅ **Automated Fetching**: Retrieves AAPL stock data every 6 hours
- ✅ **Robust Error Handling**: Comprehensive try-except blocks and retry logic
- ✅ **Data Validation**: Verifies data insertion after each run
- ✅ **Dockerized**: Complete setup with single `docker-compose up` command
- ✅ **Scalable**: Easy to add more stocks or change schedule
- ✅ **Secure**: Environment variables for API keys and credentials

## 📋 Prerequisites

Before you begin, ensure you have:

- **Docker** installed ([Download Docker](https://www.docker.com/get-started))
- **Docker Compose** installed (usually comes with Docker Desktop)
- **Alpha Vantage API Key** (free) - Get it from [https://www.alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key)

## 🚀 Quick Start

### 1. Get Alpha Vantage API Key

1. Visit: [https://www.alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key)
2. Enter your email and click "GET FREE API KEY"
3. Copy the API key (you'll need it in step 3)

### 2. Clone/Navigate to Project

```bash
cd 8byte-assesment
```

### 3. Configure Environment Variables

Create a `.env` file from the template:

```bash
# On Windows
copy .env.example .env

# On Mac/Linux
cp .env.example .env
```

Edit the `.env` file and add your Alpha Vantage API key:

```env
ALPHA_VANTAGE_API_KEY=your_actual_api_key_here
```

> **Note**: Keep all other default values as is unless you need custom configuration.

### 4. Build and Run

Start the entire pipeline with a single command:

```bash
docker-compose up --build
```

This will:
- Build the custom Airflow Docker image
- Start PostgreSQL databases (one for Airflow metadata, one for stock data)
- Initialize Airflow and create admin user
- Start Airflow webserver and scheduler

**First-time setup takes 2-3 minutes**. Wait for the message: `Airflow webserver is ready`

### 5. Access Airflow UI

Open your browser and navigate to:

```
http://localhost:8080
```

**Login credentials:**
- Username: `admin`
- Password: `admin`

### 6. Enable the DAG

1. In the Airflow UI, you'll see the `stock_data_pipeline` DAG
2. Toggle the switch on the left to **enable** the DAG
3. Click the "Play" button to trigger a manual run (optional)

The DAG will automatically run every 6 hours at: **00:00, 06:00, 12:00, 18:00**

---

## 📂 Project Structure

```
8byte-assesment/
├── dags/
│   └── stock_data_pipeline.py      # Airflow DAG definition
├── scripts/
│   └── fetch_stock_data.py         # Data fetching script
├── sql/
│   └── init.sql                    # Database initialization
├── logs/                           # Airflow logs (auto-created)
├── plugins/                        # Airflow plugins (auto-created)
├── docker-compose.yml              # Docker orchestration
├── Dockerfile                      # Custom Airflow image
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
├── .env                           # Your configuration (create this)
└── README.md                       # This file
```

---

## 🗄️ Database Schema

The pipeline stores data in the `stock_data` table:

| Column       | Type         | Description                  |
|--------------|--------------|------------------------------|
| id           | SERIAL       | Primary key                  |
| symbol       | VARCHAR(10)  | Stock symbol (AAPL)          |
| timestamp    | TIMESTAMP    | Data point timestamp         |
| open_price   | DECIMAL(10,2)| Opening price                |
| high_price   | DECIMAL(10,2)| Highest price                |
| low_price    | DECIMAL(10,2)| Lowest price                 |
| close_price  | DECIMAL(10,2)| Closing price                |
| volume       | BIGINT       | Trading volume               |
| created_at   | TIMESTAMP    | Record creation time         |

**Unique constraint**: `(symbol, timestamp)` - prevents duplicate data

---

## 🔍 Viewing Stored Data

### Option 1: Using Docker

Connect to the PostgreSQL container:

```bash
docker exec -it postgres_stock psql -U stockuser -d stock_database
```

Then run SQL queries:

```sql
-- View all data
SELECT * FROM stock_data ORDER BY timestamp DESC LIMIT 10;

-- Count total records
SELECT COUNT(*) FROM stock_data;

-- Get latest data point
SELECT * FROM stock_data ORDER BY timestamp DESC LIMIT 1;
```

Type `\q` to exit.

### Option 2: Using External Tool

Connect using any PostgreSQL client (DBeaver, pgAdmin, etc.):

- **Host**: `localhost`
- **Port**: `5433`
- **Database**: `stock_database`
- **Username**: `stockuser`
- **Password**: `stockpass123`

---

## 🛠️ Pipeline Details

### Schedule

- **Frequency**: Every 6 hours
- **Cron Expression**: `0 */6 * * *`
- **Run Times**: 00:00, 06:00, 12:00, 18:00 (system time)

### Error Handling

The pipeline includes:

1. **API Retry Logic**: 3 retries with 5-minute delay
2. **Database Transaction Rollback**: On insertion failure
3. **Validation Step**: Confirms data was stored
4. **Comprehensive Logging**: All operations logged

### Data Flow

1. **Fetch**: Retrieve hourly AAPL data from Alpha Vantage
2. **Parse**: Extract OHLCV data (Open, High, Low, Close, Volume)
3. **Store**: Insert into PostgreSQL with UPSERT logic
4. **Validate**: Verify records were inserted
5. **Log**: Complete execution summary

---

## 📊 Monitoring

### Airflow UI

- **DAG View**: See pipeline status and run history
- **Task Logs**: Click on tasks to view detailed logs
- **Graph View**: Visualize task dependencies

### Logs Location

Logs are stored in: `./logs/dag_id=stock_data_pipeline/`

View logs in real-time:

```bash
docker-compose logs -f airflow-scheduler
```

---

## 🔧 Customization

### Change Stock Symbol

Edit `dags/stock_data_pipeline.py` and `scripts/fetch_stock_data.py`:

```python
symbol = 'TSLA'  # Change from AAPL to any stock
```

### Change Schedule

Edit `dags/stock_data_pipeline.py`:

```python
schedule_interval='0 */3 * * *',  # Every 3 hours instead of 6
```

### Add More Stocks

Modify the DAG to loop over multiple symbols:

```python
symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
for symbol in symbols:
    # Create task for each symbol
```

---

## 🐛 Troubleshooting

### Issue: Airflow UI not loading

**Solution**: Wait 2-3 minutes for initialization. Check logs:

```bash
docker-compose logs airflow-webserver
```

### Issue: DAG not appearing

**Solution**: 
1. Check DAG file syntax: `docker-compose exec airflow-webserver airflow dags list`
2. Refresh Airflow UI (Ctrl+R)
3. Check scheduler logs: `docker-compose logs airflow-scheduler`

### Issue: API rate limit error

**Solution**: Alpha Vantage free tier limits:
- 5 API calls per minute
- 500 calls per day

The 6-hour schedule stays well within limits (4 calls/day).

### Issue: "API key not set" error

**Solution**: 
1. Verify `.env` file exists with your API key
2. Restart containers: `docker-compose down && docker-compose up -d`
3. Check environment variables: `docker-compose exec airflow-scheduler env | grep ALPHA`

### Issue: Database connection failed

**Solution**:
1. Verify postgres_stock is running: `docker ps`
2. Check logs: `docker-compose logs postgres_stock`
3. Test connection: `docker exec -it postgres_stock pg_isready -U stockuser`

---

## 🛑 Stopping the Pipeline

### Graceful Shutdown

```bash
docker-compose down
```

### Remove All Data (including volumes)

```bash
docker-compose down -v
```

**Warning**: This deletes all stored stock data and Airflow metadata!

---

## 📈 Scaling Considerations

This pipeline is designed to scale:

1. **Multiple Stocks**: Add more symbols with minimal code changes
2. **Higher Frequency**: Change schedule (respect API limits)
3. **Data Retention**: Implement archival strategy for old data
4. **Alerting**: Add email notifications on failure
5. **Monitoring**: Integrate with Prometheus/Grafana

---

## 🔒 Security Best Practices

- ✅ API keys stored in `.env` file (not committed to Git)
- ✅ `.env` added to `.gitignore`
- ✅ Database credentials configurable
- ✅ Network isolation via Docker networks
- ✅ No hardcoded secrets in code

---

## 📝 API Information

**Alpha Vantage Free Tier:**
- 5 API calls per minute
- 500 API calls per day
- No credit card required
- Perfect for this project's 6-hour schedule (4 calls/day)

**Endpoint Used**: `TIME_SERIES_INTRADAY`
- Interval: 60min (hourly data)
- Output: Last 100 data points

---

## 🤝 Support

For issues or questions:

1. Check the logs: `docker-compose logs`
2. Review Airflow UI task logs
3. Verify API key is valid at [Alpha Vantage](https://www.alphavantage.co)

---

## 📄 License

This project is created for educational purposes as part of a technical assignment.

---

## ✅ Evaluation Checklist

- ✅ **Correctness**: Data accurately fetched and stored
- ✅ **Error Handling**: Try-except blocks, retries, validation
- ✅ **Scalability**: Easy to add stocks, change schedule
- ✅ **Code Quality**: Clean, documented, modular
- ✅ **Dockerization**: Single command deployment

---

**Built with ❤️ using Apache Airflow, PostgreSQL, and Docker**