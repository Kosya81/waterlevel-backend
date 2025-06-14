import psycopg2
from datetime import datetime
import boto3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_PARAMS = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT')
}

def get_db_metrics():
    """Collect PostgreSQL metrics"""
    metrics = {}
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        # Get total number of records
        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM stations) as stations_count,
                (SELECT COUNT(*) FROM water_levels) as water_levels_count,
                (SELECT COUNT(*) FROM temperatures) as temperatures_count
        """)
        counts = cur.fetchone()
        metrics['stations_count'] = counts[0]
        metrics['water_levels_count'] = counts[1]
        metrics['temperatures_count'] = counts[2]
        
        # Get database size
        cur.execute("""
            SELECT pg_database_size(%s)
        """, (DB_PARAMS['dbname'],))
        metrics['db_size_bytes'] = cur.fetchone()[0]
        
        # Get last update time
        cur.execute("""
            SELECT MAX(last_updated) FROM stations
        """)
        metrics['last_update'] = cur.fetchone()[0]
        
        # Get active connections
        cur.execute("""
            SELECT count(*) FROM pg_stat_activity
        """)
        metrics['active_connections'] = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return metrics
        
    except Exception as e:
        print(f"Error collecting metrics: {str(e)}")
        return None

def send_metrics_to_cloudwatch(metrics):
    """Send metrics to CloudWatch"""
    if not metrics:
        return
    
    # Get AWS region from environment or use default
    region = os.getenv('AWS_DEFAULT_REGION', 'eu-central-1')
    
    # Create CloudWatch client with explicit region
    cloudwatch = boto3.client('cloudwatch', region_name=region)
    
    # Convert metrics to CloudWatch format
    metric_data = []
    timestamp = datetime.utcnow()
    
    for name, value in metrics.items():
        if isinstance(value, datetime):
            value = value.timestamp()
        
        metric_data.append({
            'MetricName': name,
            'Value': value,
            'Unit': 'Count',
            'Timestamp': timestamp,
            'Dimensions': [
                {
                    'Name': 'Database',
                    'Value': DB_PARAMS['dbname']
                }
            ]
        })
    
    # Send metrics to CloudWatch
    try:
        cloudwatch.put_metric_data(
            Namespace='WaterLevel/PostgreSQL',
            MetricData=metric_data
        )
        print("Metrics sent successfully")
    except Exception as e:
        print(f"Error sending metrics to CloudWatch: {str(e)}")

if __name__ == "__main__":
    metrics = get_db_metrics()
    if metrics:
        send_metrics_to_cloudwatch(metrics) 