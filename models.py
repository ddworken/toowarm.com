"""
Database models for storing weather data using SQLAlchemy.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class WeatherForecast(Base):
    """Model for storing weather forecast data for Franklin Falls."""

    __tablename__ = 'weather_forecasts'

    id = Column(Integer, primary_key=True)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    period_name = Column(String(100), nullable=False)
    temperature = Column(Integer, nullable=False)
    temperature_unit = Column(String(1), nullable=False)  # F or C
    wind_speed = Column(String(50), nullable=False)
    wind_direction = Column(String(10), nullable=False)
    short_forecast = Column(String(200), nullable=False)
    detailed_forecast = Column(Text, nullable=False)

    # Additional metadata
    grid_x = Column(Integer)
    grid_y = Column(Integer)
    grid_id = Column(String(10))

    def __repr__(self):
        return f"<WeatherForecast(period='{self.period_name}', temp={self.temperature}°{self.temperature_unit}, fetched={self.fetched_at})>"


def get_db_engine(database_url='sqlite:///franklin_falls_weather.db'):
    """
    Create and return a database engine.

    Args:
        database_url: Database URL. Defaults to SQLite, but can be changed to PostgreSQL.
                     Example PostgreSQL URL: 'postgresql://user:password@localhost/dbname'

    Returns:
        SQLAlchemy engine instance
    """
    engine = create_engine(database_url, echo=False)
    return engine


def init_db(database_url='sqlite:///franklin_falls_weather.db'):
    """
    Initialize the database by creating all tables.

    Args:
        database_url: Database URL

    Returns:
        Tuple of (engine, SessionLocal)
    """
    engine = get_db_engine(database_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return engine, SessionLocal


def get_session(database_url='sqlite:///franklin_falls_weather.db'):
    """
    Get a database session.

    Args:
        database_url: Database URL

    Returns:
        SQLAlchemy session
    """
    _, SessionLocal = init_db(database_url)
    return SessionLocal()
