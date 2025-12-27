"""
Database models for storing weather data using SQLAlchemy.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class WeatherForecast(Base):
    """Model for storing weather forecast data for multiple ice climbing locations."""

    __tablename__ = 'weather_forecasts'

    id = Column(Integer, primary_key=True)

    # Location information
    location_name = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

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
        return f"<WeatherForecast(location='{self.location_name}', period='{self.period_name}', temp={self.temperature}°{self.temperature_unit}, fetched={self.fetched_at})>"


class AvalancheForecast(Base):
    """Model for storing NWAC avalanche forecast data."""

    __tablename__ = 'avalanche_forecasts'

    id = Column(Integer, primary_key=True)

    # Zone information
    zone_id = Column(String(10), nullable=False, index=True)
    zone_name = Column(String(100), nullable=False)

    # Forecast date (the date this forecast is for)
    forecast_date = Column(Date, nullable=False, index=True)

    # Danger rating info
    danger_rating = Column(Integer, nullable=True)  # -1 for no rating, 1-5 for Low to Extreme
    danger_level_text = Column(String(50), nullable=True)  # "low", "moderate", "considerable", "high", "extreme", "no rating"

    # Metadata
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    product_type = Column(String(50), nullable=True)  # "forecast", "summary", etc.

    # Flag for "no forecast available"
    no_forecast = Column(Integer, default=0)  # 1 if API returned empty array

    def __repr__(self):
        return f"<AvalancheForecast(zone='{self.zone_name}', date={self.forecast_date}, danger={self.danger_level_text})>"


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
