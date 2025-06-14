from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    code = Column(String)
    river = Column(String)
    region = Column(String)
    coordinates = Column(String)
    graph_url = Column(String)
    last_updated = Column(DateTime)
    time_offset = Column(Integer, default=0)  # Смещение времени в секундах

class WaterLevel(Base):
    __tablename__ = "water_levels"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"))
    timestamp = Column(DateTime)
    timestamp_utc = Column(DateTime)  # UTC timestamp
    value = Column(Float)

class Temperature(Base):
    __tablename__ = "temperatures"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"))
    timestamp = Column(DateTime)
    timestamp_utc = Column(DateTime)  # UTC timestamp
    value = Column(Float) 