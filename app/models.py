from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    river = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    measurements = relationship("Measurement", back_populates="station")

class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"))
    timestamp = Column(DateTime, index=True)
    water_level = Column(Float)
    station = relationship("Station", back_populates="measurements") 