from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas

def get_station(db: Session, station_id: int):
    return db.query(models.Station).filter(models.Station.id == station_id).first()

def get_stations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Station).offset(skip).limit(limit).all()

def create_station(db: Session, station: schemas.StationCreate):
    db_station = models.Station(
        name=station.name,
        code=station.code,
        river=station.river,
        region=station.region,
        coordinates=station.coordinates,
        graph_url=station.graph_url,
        last_updated=datetime.now()
    )
    db.add(db_station)
    db.commit()
    db.refresh(db_station)
    return db_station

def get_water_levels(
    db: Session,
    station_id: int,
    start_date: datetime = None,
    end_date: datetime = None,
    skip: int = 0,
    limit: int = 1000
):
    query = db.query(models.WaterLevel).filter(models.WaterLevel.station_id == station_id)
    
    if start_date:
        query = query.filter(models.WaterLevel.timestamp_utc >= start_date)
    if end_date:
        query = query.filter(models.WaterLevel.timestamp_utc <= end_date)
    
    water_levels = query.order_by(models.WaterLevel.timestamp_utc.asc()).offset(skip).limit(limit).all()
    
    # Загружаем информацию о станции
    for level in water_levels:
        level.station = get_station(db, station_id)
    
    return water_levels

def get_temperatures(
    db: Session,
    station_id: int,
    start_date: datetime = None,
    end_date: datetime = None,
    skip: int = 0,
    limit: int = 1000
):
    query = db.query(models.Temperature).filter(models.Temperature.station_id == station_id)
    
    if start_date:
        query = query.filter(models.Temperature.timestamp_utc >= start_date)
    if end_date:
        query = query.filter(models.Temperature.timestamp_utc <= end_date)
    
    temperatures = query.order_by(models.Temperature.timestamp_utc.asc()).offset(skip).limit(limit).all()
    
    # Загружаем информацию о станции
    for temp in temperatures:
        temp.station = get_station(db, station_id)
    
    return temperatures 