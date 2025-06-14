import logging
import watchtower
import os
from datetime import datetime

def setup_logging(service_name):
    """Setup logging configuration with CloudWatch integration"""
    
    # Create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # CloudWatch handler
    try:
        cloudwatch_handler = watchtower.CloudWatchLogHandler(
            log_group=f"/waterlevel/{service_name}",
            stream_name=datetime.now().strftime("%Y-%m-%d"),
            create_log_group=True
        )
        cloudwatch_handler.setFormatter(formatter)
        logger.addHandler(cloudwatch_handler)
    except Exception as e:
        logger.error(f"Failed to setup CloudWatch logging: {str(e)}")
    
    return logger 