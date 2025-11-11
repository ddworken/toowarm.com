#!/usr/bin/env python3
"""
Long-running job to periodically collect and store weather forecast data
for Franklin Falls, Washington using the National Weather Service API.
"""

import requests
import json
import time
import logging
from datetime import datetime
from models import WeatherForecast, init_db

# Franklin Falls, Washington coordinates
LATITUDE = 47.4254
LONGITUDE = -121.4320

# API endpoints
BASE_URL = "https://api.weather.gov"

# User-Agent header is required by NWS API
HEADERS = {
    "User-Agent": "(Franklin Falls Weather Collector, weather@example.com)"
}

# Fetch interval (in seconds) - default: every 1 hour
FETCH_INTERVAL = 3600

# Database URL - can be changed to PostgreSQL later
DATABASE_URL = 'sqlite:///franklin_falls_weather.db'

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_and_store_weather():
    """
    Fetch weather forecast for Franklin Falls and store it in the database.

    Returns:
        bool: True if successful, False otherwise
    """
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
            logger.info(f"Successfully stored {records_added} forecast periods in database")

            # Print summary
            first_period = periods[0]
            logger.info(f"Current forecast: {first_period['name']} - "
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
    except KeyError as e:
        logger.error(f"Error parsing response data: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def run_collector(interval=FETCH_INTERVAL, run_once=False):
    """
    Run the weather collector as a long-running job.

    Args:
        interval: Time between fetches in seconds (default: 3600 = 1 hour)
        run_once: If True, only fetch once and exit (useful for testing)
    """
    logger.info("="*70)
    logger.info("Franklin Falls Weather Collector Starting")
    logger.info("="*70)
    logger.info(f"Database: {DATABASE_URL}")
    logger.info(f"Fetch interval: {interval} seconds ({interval/60:.1f} minutes)")
    logger.info(f"Run once mode: {run_once}")
    logger.info("="*70)

    # Initialize database
    logger.info("Initializing database...")
    init_db(DATABASE_URL)
    logger.info("Database initialized successfully")

    iteration = 0

    while True:
        iteration += 1
        logger.info(f"\n--- Fetch iteration #{iteration} ---")

        success = fetch_and_store_weather()

        if success:
            logger.info("Fetch completed successfully")
        else:
            logger.warning("Fetch failed, will retry at next interval")

        if run_once:
            logger.info("Run-once mode enabled, exiting...")
            break

        logger.info(f"Sleeping for {interval} seconds until next fetch...")
        logger.info(f"Next fetch at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("\nReceived interrupt signal, shutting down gracefully...")
            break

    logger.info("Weather collector stopped")


if __name__ == "__main__":
    import sys

    # Check for command-line arguments
    run_once = '--once' in sys.argv or '-o' in sys.argv

    # Allow custom interval via command line
    interval = FETCH_INTERVAL
    for arg in sys.argv[1:]:
        if arg.startswith('--interval='):
            try:
                interval = int(arg.split('=')[1])
                logger.info(f"Custom interval set: {interval} seconds")
            except ValueError:
                logger.error("Invalid interval value, using default")

    run_collector(interval=interval, run_once=run_once)
