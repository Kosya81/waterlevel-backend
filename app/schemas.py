from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class MeasurementBase(BaseModel):
    timestamp: datetime
    water_level: float

class MeasurementCreate(MeasurementBase):
    station_id: int

class Measurement(MeasurementBase):
    id: int
    station_id: int

    class Config:
        from_attributes = True

class StationBase(BaseModel):
    name: str
    river: str
    latitude: float
    longitude: float

class StationCreate(StationBase):
    pass

class Station(StationBase):
    id: int
    measurements: List[Measurement] = []

    class Config:
        from_attributes = True 