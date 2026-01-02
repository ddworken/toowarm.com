"""
Database models for storing weather data using SQLAlchemy.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Date, Index
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

    # Snow accumulation (from gridpoints API, in millimeters)
    snow_accumulation_mm = Column(Float, nullable=True)

    # Period timing (for matching with gridpoints data)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)

    # Additional metadata
    grid_x = Column(Integer)
    grid_y = Column(Integer)
    grid_id = Column(String(10))

    # Composite index for efficient queries filtering by location + time range
    __table_args__ = (
        Index('ix_weather_location_fetched', 'location_name', 'fetched_at'),
    )

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

    # Elevation band (for elevation-specific forecasts)
    elevation_band = Column(String(10), nullable=True, index=True)  # 'lower', 'middle', 'upper', or None for overall

    # Danger rating info
    danger_rating = Column(Integer, nullable=True)  # -1 for no rating, 1-5 for Low to Extreme
    danger_level_text = Column(String(50), nullable=True)  # "low", "moderate", "considerable", "high", "extreme", "no rating"

    # Elevation breakdown ratings (cached to avoid re-fetching)
    danger_lower = Column(Integer, nullable=True)  # Danger rating for lower elevation band
    danger_middle = Column(Integer, nullable=True)  # Danger rating for middle elevation band
    danger_upper = Column(Integer, nullable=True)  # Danger rating for upper elevation band

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

    # Enable WAL mode and performance pragmas for SQLite
    if database_url.startswith('sqlite'):
        from sqlalchemy import event

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB page cache
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
            cursor.execute("PRAGMA temp_store=MEMORY")  # Keep temp tables in RAM
            cursor.execute("PRAGMA synchronous=NORMAL")  # Faster syncs (safe with WAL)
            cursor.close()

    return engine


# Cache for engine and session factory (singleton pattern)
_engine_cache = {}
_session_factory_cache = {}


def init_db(database_url='sqlite:///franklin_falls_weather.db'):
    """
    Initialize the database by creating all tables.
    Uses cached engine if available.

    Args:
        database_url: Database URL

    Returns:
        Tuple of (engine, SessionLocal)
    """
    global _engine_cache, _session_factory_cache

    # Return cached engine/factory if available
    if database_url in _engine_cache:
        return _engine_cache[database_url], _session_factory_cache[database_url]

    engine = get_db_engine(database_url)
    Base.metadata.create_all(engine)

    # Create additional indexes for performance if using SQLite
    if database_url.startswith('sqlite'):
        from sqlalchemy import text
        with engine.connect() as conn:
            # Covering index for the heavy all_periods query
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_weather_location_fetched_period ON weather_forecasts (location_name, fetched_at, period_name)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_weather_covering ON weather_forecasts (location_name, fetched_at, temperature, wind_speed, short_forecast, period_name)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_avalanche_zone_date_band ON avalanche_forecasts (zone_id, forecast_date, elevation_band)"))
            conn.commit()

    SessionLocal = sessionmaker(bind=engine)

    # Cache for future calls
    _engine_cache[database_url] = engine
    _session_factory_cache[database_url] = SessionLocal

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
