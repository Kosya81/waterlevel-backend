from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/stations/", response_model=List[schemas.Station])
def read_stations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    stations = crud.get_stations(db, skip=skip, limit=limit)
    return stations

@app.get("/stations/{station_id}", response_model=schemas.Station)
def read_station(station_id: int, db: Session = Depends(get_db)):
    db_station = crud.get_station(db, station_id=station_id)
    if db_station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    return db_station

@app.post("/stations/", response_model=schemas.Station)
def create_station(station: schemas.StationCreate, db: Session = Depends(get_db)):
    return crud.create_station(db=db, station=station)

@app.get("/stations/{station_id}/measurements/", response_model=List[schemas.Measurement])
def read_measurements(
    station_id: int,
    start_date: datetime = None,
    end_date: datetime = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    measurements = crud.get_measurements(
        db,
        station_id=station_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return measurements

@app.post("/stations/{station_id}/measurements/", response_model=schemas.Measurement)
def create_measurement(
    station_id: int,
    measurement: schemas.MeasurementCreate,
    db: Session = Depends(get_db)
):
    if crud.get_station(db, station_id=station_id) is None:
        raise HTTPException(status_code=404, detail="Station not found")
    return crud.create_measurement(db=db, measurement=measurement) 