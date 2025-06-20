import asyncio
import aiohttp
import json
import re
from datetime import datetime, timezone, timedelta
import sys
import os
import logging
from logging.handlers import RotatingFileHandler

# Добавляем родительскую директорию в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import SessionLocal
from app import models
from scrape_stations import get_station_data, preprocess_js_object
from app.logging_config import setup_logging

# Настройка логирования
logger = setup_logging("scheduler")

async def process_station(session, station_code, station_name, db):
    """Process single station and save its measurements to database"""
    try:
        logger.info(f"Fetching data for station {station_name} ({station_code})...")
        data = get_station_data(station_code, station_name)
        
        if not data:
            logger.warning(f"No data for station {station_name}")
            return
        
        # Get station from database
        station = db.query(models.Station).filter(models.Station.code == station_code).first()
        if not station:
            logger.warning(f"Station {station_name} not found in database")
            return
        
        # Объединяем данные уровня воды и температуры по timestamp
        measurements_by_time = {}
        
        # Process water level data
        if data['water_level'] and data['timestamps']:
            for timestamp, level in zip(data['timestamps'], data['water_level']):
                if level is not None:  # Skip None values
                    timestamp_str = timestamp.isoformat()
                    if timestamp_str not in measurements_by_time:
                        measurements_by_time[timestamp_str] = {'water_level': None, 'temperature': None}
                    measurements_by_time[timestamp_str]['water_level'] = level
        
        # Process temperature data
        if data['temperature'] and data['timestamps']:
            for timestamp, temp in zip(data['timestamps'], data['temperature']):
                if temp is not None:  # Skip None values
                    timestamp_str = timestamp.isoformat()
                    if timestamp_str not in measurements_by_time:
                        measurements_by_time[timestamp_str] = {'water_level': None, 'temperature': None}
                    measurements_by_time[timestamp_str]['temperature'] = temp
        
        # Save measurements to database
        water_level_count = 0
        temperature_count = 0
        
        for timestamp_str, data in measurements_by_time.items():
            timestamp = datetime.fromisoformat(timestamp_str)
            # Применяем смещение времени станции (по умолчанию 0)
            time_offset = station.time_offset or 0
            timestamp_utc = timestamp + timedelta(seconds=time_offset)
            
            # Save water level if available
            if data['water_level'] is not None:
                # Check if measurement already exists
                existing_water_level = db.query(models.WaterLevel).filter(
                    models.WaterLevel.station_id == station.id,
                    models.WaterLevel.timestamp == timestamp
                ).first()
                
                if not existing_water_level:
                    water_level = models.WaterLevel(
                        station_id=station.id,
                        timestamp=timestamp,
                        timestamp_utc=timestamp_utc,
                        value=data['water_level']
                    )
                    db.add(water_level)
                    water_level_count += 1
            
            # Save temperature if available
            if data['temperature'] is not None:
                # Check if measurement already exists
                existing_temperature = db.query(models.Temperature).filter(
                    models.Temperature.station_id == station.id,
                    models.Temperature.timestamp == timestamp
                ).first()
                
                if not existing_temperature:
                    temperature = models.Temperature(
                        station_id=station.id,
                        timestamp=timestamp,
                        timestamp_utc=timestamp_utc,
                        value=data['temperature']
                    )
                    db.add(temperature)
                    temperature_count += 1
        
        # Update station's last_updated timestamp
        station.last_updated = datetime.now()
        
        # Commit changes
        db.commit()
        logger.info(f"Station {station_name}: Added {water_level_count} water levels and {temperature_count} temperatures")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing station {station_name}: {str(e)}")

async def update_all_stations():
    """Update measurements for all stations"""
    db = SessionLocal()
    try:
        # Get all stations from database
        stations = db.query(models.Station).all()
        
        if not stations:
            logger.warning("No stations found in the database")
            return
        
        logger.info(f"Found {len(stations)} stations")
        
        # Process each station
        async with aiohttp.ClientSession() as session:
            tasks = []
            for station in stations:
                task = asyncio.create_task(process_station(session, station.code, station.name, db))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
        
        logger.info("Data update completed")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(update_all_stations()) 