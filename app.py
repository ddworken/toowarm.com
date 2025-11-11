#!/usr/bin/env python3
"""
Main application entry point that runs both the Flask web server
and the weather data collector in the background.
"""

import threading
import logging
import time
from flask import Flask, render_template
from datetime import datetime, timedelta
from sqlalchemy import func
from models import WeatherForecast, get_session, init_db
import requests
import re

# Configuration
LATITUDE = 47.4254
LONGITUDE = -121.4320
BASE_URL = "https://api.weather.gov"
HEADERS = {"User-Agent": "(Franklin Falls Weather Collector, weather@example.com)"}
FETCH_INTERVAL = 3600  # 1 hour
DATABASE_URL = 'sqlite:///franklin_falls_weather.db'

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)


# ============================================================================
# Weather Data Collection Functions
# ============================================================================

def fetch_and_store_weather():
    """Fetch weather forecast and store it in the database."""
    logger.info(f"Fetching weather data for Franklin Falls, WA ({LATITUDE}, {LONGITUDE})")

    try:
        # Step 1: Get grid point information
        points_url = f"{BASE_URL}/points/{LATITUDE},{LONGITUDE}"
        response = requests.get(points_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        points_data = response.json()

        # Extract grid information and forecast URL
        grid_id = points_data['properties']['gridId']
        grid_x = points_data['properties']['gridX']
        grid_y = points_data['properties']['gridY']
        forecast_url = points_data['properties']['forecast']

        logger.info(f"Grid info: {grid_id}/{grid_x},{grid_y}")

        # Step 2: Get the actual forecast
        forecast_response = requests.get(forecast_url, headers=HEADERS, timeout=10)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        periods = forecast_data['properties']['periods']

        # Step 3: Store in database
        _, SessionLocal = init_db(DATABASE_URL)
        session = SessionLocal()

        try:
            fetched_at = datetime.utcnow()
            records_added = 0

            for period in periods:
                weather_record = WeatherForecast(
                    fetched_at=fetched_at,
                    period_name=period['name'],
                    temperature=period['temperature'],
                    temperature_unit=period['temperatureUnit'],
                    wind_speed=period['windSpeed'],
                    wind_direction=period['windDirection'],
                    short_forecast=period['shortForecast'],
                    detailed_forecast=period['detailedForecast'],
                    grid_id=grid_id,
                    grid_x=grid_x,
                    grid_y=grid_y
                )
                session.add(weather_record)
                records_added += 1

            session.commit()
            logger.info(f"Successfully stored {records_added} forecast periods")

            first_period = periods[0]
            logger.info(f"Current: {first_period['name']} - "
                       f"{first_period['temperature']}°{first_period['temperatureUnit']}, "
                       f"{first_period['shortForecast']}")

            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            return False
        finally:
            session.close()

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def weather_collector_worker():
    """Background worker that periodically fetches weather data."""
    logger.info("="*70)
    logger.info("Weather Collector Starting")
    logger.info("="*70)
    logger.info(f"Database: {DATABASE_URL}")
    logger.info(f"Fetch interval: {FETCH_INTERVAL} seconds ({FETCH_INTERVAL/60:.1f} minutes)")
    logger.info("="*70)

    # Initialize database
    init_db(DATABASE_URL)
    logger.info("Database initialized")

    # Fetch immediately on startup
    fetch_and_store_weather()

    iteration = 1
    while True:
        try:
            time.sleep(FETCH_INTERVAL)
            iteration += 1
            logger.info(f"--- Fetch iteration #{iteration} ---")
            fetch_and_store_weather()
        except Exception as e:
            logger.error(f"Error in collector worker: {e}")


# ============================================================================
# Web Application Functions
# ============================================================================

def parse_wind_speed(wind_str):
    """Extract numeric wind speed from string like '5 to 10 mph'."""
    if not wind_str:
        return 0
    match = re.search(r'(\d+)', wind_str)
    if match:
        return int(match.group(1))
    return 0


def get_temp_color(temp):
    """Get color class based on temperature for ice climbing."""
    if temp <= 20:
        return 'temp-excellent'
    elif temp <= 32:
        return 'temp-good'
    elif temp <= 40:
        return 'temp-marginal'
    else:
        return 'temp-poor'


def get_forecast_color(forecast_text):
    """Get color class based on forecast conditions."""
    forecast_lower = forecast_text.lower()

    if 'snow' in forecast_lower and 'rain' not in forecast_lower:
        return 'condition-excellent'
    elif 'snow' in forecast_lower and 'rain' in forecast_lower:
        return 'condition-marginal'
    elif 'rain' in forecast_lower:
        return 'condition-poor'
    elif 'sunny' in forecast_lower or 'clear' in forecast_lower:
        return 'condition-good'
    else:
        return 'condition-neutral'


def get_wind_color(wind_speed):
    """Get color class based on wind speed."""
    if wind_speed <= 5:
        return 'wind-excellent'
    elif wind_speed <= 10:
        return 'wind-good'
    elif wind_speed <= 15:
        return 'wind-marginal'
    else:
        return 'wind-poor'


def get_historical_data(days=7):
    """Get historical weather data for the past N days."""
    session = get_session(DATABASE_URL)

    try:
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        # Get all distinct fetch times in the past N days
        fetch_times = session.query(WeatherForecast.fetched_at).filter(
            WeatherForecast.fetched_at >= cutoff_time
        ).distinct().order_by(WeatherForecast.fetched_at).all()

        historical_data = []

        for (fetch_time,) in fetch_times:
            # Get the first period from each fetch
            forecast = session.query(WeatherForecast).filter(
                WeatherForecast.fetched_at == fetch_time
            ).first()

            if forecast:
                historical_data.append({
                    'date': fetch_time,
                    'period_name': forecast.period_name,
                    'temperature': forecast.temperature,
                    'temperature_unit': forecast.temperature_unit,
                    'wind_speed': parse_wind_speed(forecast.wind_speed),
                    'wind_speed_str': forecast.wind_speed,
                    'short_forecast': forecast.short_forecast,
                    'detailed_forecast': forecast.detailed_forecast
                })

        return historical_data

    finally:
        session.close()


def get_future_forecast():
    """Get the latest future forecast."""
    session = get_session(DATABASE_URL)

    try:
        # Get the most recent fetch
        latest_fetch = session.query(func.max(WeatherForecast.fetched_at)).scalar()

        if not latest_fetch:
            return []

        # Get all periods from the latest fetch
        forecasts = session.query(WeatherForecast).filter(
            WeatherForecast.fetched_at == latest_fetch
        ).order_by(WeatherForecast.id).all()

        forecast_data = []
        for forecast in forecasts:
            forecast_data.append({
                'period_name': forecast.period_name,
                'temperature': forecast.temperature,
                'temperature_unit': forecast.temperature_unit,
                'wind_speed': parse_wind_speed(forecast.wind_speed),
                'wind_speed_str': forecast.wind_speed,
                'short_forecast': forecast.short_forecast,
                'detailed_forecast': forecast.detailed_forecast
            })

        return forecast_data

    finally:
        session.close()


@app.route('/')
def index():
    """Main page showing weather conditions for ice climbing."""
    # Get historical data (past 7 days)
    historical = get_historical_data(days=7)

    # Get future forecast
    future = get_future_forecast()

    # Combine and prepare for display
    all_periods = []

    # Add historical data
    for h in historical:
        all_periods.append({
            'is_historical': True,
            'date': h['date'].strftime('%a %m/%d'),
            'period_name': h['period_name'],
            'temperature': h['temperature'],
            'temp_color': get_temp_color(h['temperature']),
            'wind_speed': h['wind_speed'],
            'wind_speed_str': h['wind_speed_str'],
            'wind_color': get_wind_color(h['wind_speed']),
            'short_forecast': h['short_forecast'],
            'forecast_color': get_forecast_color(h['short_forecast']),
            'detailed_forecast': h['detailed_forecast']
        })

    # Add future forecast
    for f in future:
        all_periods.append({
            'is_historical': False,
            'date': '',
            'period_name': f['period_name'],
            'temperature': f['temperature'],
            'temp_color': get_temp_color(f['temperature']),
            'wind_speed': f['wind_speed'],
            'wind_speed_str': f['wind_speed_str'],
            'wind_color': get_wind_color(f['wind_speed']),
            'short_forecast': f['short_forecast'],
            'forecast_color': get_forecast_color(f['short_forecast']),
            'detailed_forecast': f['detailed_forecast']
        })

    return render_template('index.html', periods=all_periods)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point that starts both the collector and web server."""
    logger.info("="*70)
    logger.info("STARTING TOO WARM - Franklin Falls Ice Climbing Weather")
    logger.info("="*70)

    # Start weather collector in background thread
    collector_thread = threading.Thread(
        target=weather_collector_worker,
        daemon=True,
        name="WeatherCollector"
    )
    collector_thread.start()
    logger.info("Weather collector thread started")

    # Give the collector a moment to initialize
    time.sleep(2)

    # Start Flask web server (blocks here)
    logger.info("Starting Flask web server on http://0.0.0.0:5000")
    logger.info("="*70)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
