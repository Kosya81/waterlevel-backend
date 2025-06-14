from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

class StationBase(BaseModel):
    name: str
    code: str
    river: str
    region: str
    coordinates: Optional[str] = None
    graph_url: str
    time_offset: Optional[int] = 0  # Смещение времени в секундах

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
    class Config:
        from_attributes = True

class TemperatureBase(BaseModel):
    station_id: int
    timestamp: datetime
    value: float

class TemperatureCreate(TemperatureBase):
    pass

class Temperature(TemperatureBase):
    class Config:
        from_attributes = True 