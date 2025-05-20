from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas

def get_station(db: Session, station_id: int):
    return db.query(models.Station).filter(models.Station.id == station_id).first()

def get_stations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Station).offset(skip).limit(limit).all()

def create_station(db: Session, station: schemas.StationCreate):
    db_station = models.Station(**station.model_dump())
    db.add(db_station)
    db.commit()
    db.refresh(db_station)
    return db_station

def get_measurements(
    db: Session, 
    station_id: int, 
    start_date: datetime = None, 
    end_date: datetime = None,
    skip: int = 0, 
    limit: int = 1000
):
    query = db.query(models.Measurement).filter(models.Measurement.station_id == station_id)
    
    if start_date:
        query = query.filter(models.Measurement.timestamp >= start_date)
    if end_date:
        query = query.filter(models.Measurement.timestamp <= end_date)
    
    return query.order_by(models.Measurement.timestamp).offset(skip).limit(limit).all()

def create_measurement(db: Session, measurement: schemas.MeasurementCreate):
    db_measurement = models.Measurement(**measurement.model_dump())
    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)
    return db_measurement 