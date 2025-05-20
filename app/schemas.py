from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class StationBase(BaseModel):
    name: str
    code: str
    river: str
    region: str
    coordinates: str
    graph_url: str

class StationCreate(StationBase):
    pass

class Station(StationBase):
    id: int
    last_updated: datetime

    class Config:
        from_attributes = True

class WaterLevelBase(BaseModel):
    station_id: int
    timestamp: datetime
    value: float

class WaterLevelCreate(WaterLevelBase):
    pass

class WaterLevel(WaterLevelBase):
    id: int

    class Config:
        from_attributes = True

class TemperatureBase(BaseModel):
    station_id: int
    timestamp: datetime
    value: float

class TemperatureCreate(TemperatureBase):
    pass

class Temperature(TemperatureBase):
    id: int

    class Config:
        from_attributes = True 