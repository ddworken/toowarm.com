#!/usr/bin/env python3
"""
Main application entry point that runs both the Flask web server
and the weather data collector in the background.
"""

import threading
import logging
import time
import os
from flask import Flask, render_template
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_
from models import WeatherForecast, AvalancheForecast, get_session, init_db
from locations import get_all_locations, get_location_by_name, ELEVATION_CONFIG
import requests
import re

# Configuration
BASE_URL = "https://api.weather.gov"
HEADERS = {"User-Agent": "(Too Warm Ice Climbing Weather, weather@example.com)"}
NWAC_API_URL = "https://api.avalanche.org/v2/public/products"
FETCH_INTERVAL = 3600  # 1 hour
AVALANCHE_CACHE_HOURS = 6  # Cache future forecasts for 6 hours
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///ice_climbing_weather.db')

# NCEI Climate Data Online (CDO) API Configuration
# Get token from: https://www.ncdc.noaa.gov/cdo-web/token
NCEI_BASE_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2"
NCEI_TOKEN = os.environ.get('NCEI_TOKEN')  # Set via: export NCEI_TOKEN=your_token_here

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)


# ============================================================================
# Elevation Correction Functions
# ============================================================================

def apply_elevation_correction(temperature, location_name):
    """
    Apply elevation-based temperature correction using atmospheric lapse rate.

    Uses conservative lapse rate for humid Pacific Northwest winters.
    Formula: Corrected_Temp = NWS_Temp - (Elevation_Diff / 1000 * Lapse_Rate)

    When actual elevation < NWS grid elevation (negative diff):
        - Climbing site is lower than NWS forecast point
        - Should be warmer → adds positive correction

    When actual elevation > NWS grid elevation (positive diff):
        - Climbing site is higher than NWS forecast point
        - Should be colder → adds negative correction

    Args:
        temperature: NWS forecast temperature (°F)
        location_name: Name of location for elevation lookup

    Returns:
        dict with:
        - corrected_temp: Adjusted temperature (rounded to int)
        - original_temp: Original NWS temperature
        - elevation_diff: Actual - NWS elevation (ft)
        - correction_applied: Temperature adjustment (°F)
        - has_correction: Boolean if correction was significant (>threshold)
    """
    if not ELEVATION_CONFIG.get('enabled', False):
        return {
            'corrected_temp': temperature,
            'original_temp': temperature,
            'elevation_diff': 0,
            'correction_applied': 0,
            'has_correction': False
        }

    location = get_location_by_name(location_name)
    if not location:
        logger.warning(f"Location '{location_name}' not found for elevation correction")
        return {
            'corrected_temp': temperature,
            'original_temp': temperature,
            'elevation_diff': 0,
            'correction_applied': 0,
            'has_correction': False
        }

    nws_elev = location.get('nws_grid_elevation_ft', 0)
    actual_elev = location.get('actual_elevation_ft', 0)

    if nws_elev == 0 or actual_elev == 0:
        logger.warning(f"Missing elevation data for '{location_name}'")
        return {
            'corrected_temp': temperature,
            'original_temp': temperature,
            'elevation_diff': 0,
            'correction_applied': 0,
            'has_correction': False
        }

    elevation_diff = actual_elev - nws_elev
    lapse_rate = ELEVATION_CONFIG.get('lapse_rate_per_1000ft', 3.0)

    # Calculate correction (negative diff = warmer, positive diff = colder)
    correction = (elevation_diff / 1000.0) * lapse_rate
    corrected_temp = round(temperature - correction)

    # Only flag as significant if exceeds threshold
    threshold = ELEVATION_CONFIG.get('minimum_correction_threshold', 2.0)
    has_significant_correction = abs(correction) >= threshold

    return {
        'corrected_temp': corrected_temp,
        'original_temp': temperature,
        'elevation_diff': elevation_diff,
        'correction_applied': round(correction, 1),
        'has_correction': has_significant_correction
    }


# ============================================================================
# Weather Data Collection Functions
# ============================================================================

def fetch_and_store_weather(location):
    """
    Fetch weather forecast for a specific location and store it in the database.

    Args:
        location: Dict with 'name', 'latitude', 'longitude', 'description'

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Fetching weather data for {location['name']} ({location['latitude']}, {location['longitude']})")

    try:
        # Step 1: Get grid point information
        points_url = f"{BASE_URL}/points/{location['latitude']},{location['longitude']}"
        response = requests.get(points_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        points_data = response.json()

        # Extract grid information and forecast URL
        grid_id = points_data['properties']['gridId']
        grid_x = points_data['properties']['gridX']
        grid_y = points_data['properties']['gridY']
        forecast_url = points_data['properties']['forecast']

        logger.info(f"  Grid info: {grid_id}/{grid_x},{grid_y}")

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
                    location_name=location['name'],
                    latitude=location['latitude'],
                    longitude=location['longitude'],
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
            logger.info(f"  Stored {records_added} forecast periods for {location['name']}")

            first_period = periods[0]
            logger.info(f"  Current: {first_period['name']} - "
                       f"{first_period['temperature']}°{first_period['temperatureUnit']}, "
                       f"{first_period['shortForecast']}")

            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Database error for {location['name']}: {e}")
            return False
        finally:
            session.close()

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data for {location['name']}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error for {location['name']}: {e}")
        return False


def weather_collector_worker():
    """Background worker that periodically fetches weather data for all locations."""
    logger.info("="*70)
    logger.info("Weather Collector Starting")
    logger.info("="*70)
    logger.info(f"Database: {DATABASE_URL}")
    logger.info(f"Fetch interval: {FETCH_INTERVAL} seconds ({FETCH_INTERVAL/60:.1f} minutes)")

    locations = get_all_locations()
    logger.info(f"Monitoring {len(locations)} locations:")
    for loc in locations:
        logger.info(f"  - {loc['name']}")
    logger.info("="*70)

    # Initialize database
    init_db(DATABASE_URL)
    logger.info("Database initialized")

    # Fetch immediately on startup for all locations
    logger.info("\n--- Initial fetch for all locations ---")
    for location in locations:
        fetch_and_store_weather(location)

    iteration = 1
    while True:
        try:
            time.sleep(FETCH_INTERVAL)
            iteration += 1
            logger.info(f"\n--- Fetch iteration #{iteration} ---")
            for location in locations:
                fetch_and_store_weather(location)
        except Exception as e:
            logger.error(f"Error in collector worker: {e}")


# ============================================================================
# Avalanche Forecast Functions
# ============================================================================

def fetch_avalanche_forecast(zone_id, forecast_date):
    """
    Fetch avalanche forecast for a specific zone and date with smart caching.

    Caching strategy:
    - Past dates: Cache never expires (historical data)
    - Current/future dates: Cache expires after AVALANCHE_CACHE_HOURS

    Args:
        zone_id: NWAC zone ID (e.g., '3' for Snoqualmie Pass)
        forecast_date: Date object for the forecast

    Returns:
        dict with 'danger_rating', 'danger_level_text', 'zone_name', or None if no zone
    """
    if zone_id is None:
        return {
            'danger_rating': None,
            'danger_level_text': 'No forecast',
            'zone_name': 'No avalanche forecast',
            'no_forecast': True
        }

    session = get_session(DATABASE_URL)

    try:
        # Check if we have cached data
        cached = session.query(AvalancheForecast).filter(
            and_(
                AvalancheForecast.zone_id == zone_id,
                AvalancheForecast.forecast_date == forecast_date
            )
        ).first()

        today = date.today()

        # If we have cached data
        if cached:
            # For past dates, cache never expires
            if forecast_date < today:
                logger.debug(f"Using cached historical avalanche data for zone {zone_id}, {forecast_date}")
                return {
                    'danger_rating': cached.danger_rating,
                    'danger_level_text': cached.danger_level_text,
                    'zone_name': cached.zone_name,
                    'no_forecast': bool(cached.no_forecast)
                }

            # For current/future dates, check if cache is fresh
            cache_age = datetime.utcnow() - cached.fetched_at
            if cache_age.total_seconds() < AVALANCHE_CACHE_HOURS * 3600:
                logger.debug(f"Using cached current avalanche data for zone {zone_id}, {forecast_date}")
                return {
                    'danger_rating': cached.danger_rating,
                    'danger_level_text': cached.danger_level_text,
                    'zone_name': cached.zone_name,
                    'no_forecast': bool(cached.no_forecast)
                }

        # Need to fetch fresh data from API
        logger.info(f"Fetching avalanche forecast for zone {zone_id}, date {forecast_date}")

        # API expects YYYY-MM-DD format
        date_str = forecast_date.strftime('%Y-%m-%d')
        params = {
            'avalanche_center_id': 'NWAC',
            'date_start': date_str,
            'date_end': date_str
        }

        response = requests.get(NWAC_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Handle empty response (no forecast available)
        if not data or len(data) == 0:
            logger.info(f"No avalanche forecast available for zone {zone_id}, {forecast_date}")
            # Store "no forecast" in DB
            if cached:
                cached.no_forecast = 1
                cached.fetched_at = datetime.utcnow()
            else:
                new_record = AvalancheForecast(
                    zone_id=zone_id,
                    zone_name=f"Zone {zone_id}",
                    forecast_date=forecast_date,
                    danger_rating=None,
                    danger_level_text='No forecast',
                    no_forecast=1,
                    fetched_at=datetime.utcnow()
                )
                session.add(new_record)
            session.commit()

            return {
                'danger_rating': None,
                'danger_level_text': 'No forecast',
                'zone_name': f"Zone {zone_id}",
                'no_forecast': True
            }

        # Find the forecast for this zone
        zone_forecast = None
        for product in data:
            if product.get('product_type') != 'forecast':
                continue

            # Check if this product covers our zone
            forecast_zones = product.get('forecast_zone', [])
            for zone in forecast_zones:
                if zone.get('zone_id') == zone_id:
                    zone_forecast = product
                    zone_name = zone.get('name', f"Zone {zone_id}")
                    break

            if zone_forecast:
                break

        if not zone_forecast:
            logger.info(f"No forecast found for zone {zone_id} in API response")
            # Store "no forecast" in DB
            if cached:
                cached.no_forecast = 1
                cached.fetched_at = datetime.utcnow()
            else:
                new_record = AvalancheForecast(
                    zone_id=zone_id,
                    zone_name=f"Zone {zone_id}",
                    forecast_date=forecast_date,
                    danger_rating=None,
                    danger_level_text='No forecast',
                    no_forecast=1,
                    fetched_at=datetime.utcnow()
                )
                session.add(new_record)
            session.commit()

            return {
                'danger_rating': None,
                'danger_level_text': 'No forecast',
                'zone_name': f"Zone {zone_id}",
                'no_forecast': True
            }

        # Extract danger rating
        danger_rating = zone_forecast.get('danger_rating', -1)
        danger_level_text = zone_forecast.get('danger_level_text', 'unknown')

        # Store or update in DB
        if cached:
            cached.danger_rating = danger_rating
            cached.danger_level_text = danger_level_text
            cached.zone_name = zone_name
            cached.no_forecast = 0
            cached.fetched_at = datetime.utcnow()
            cached.product_type = zone_forecast.get('product_type')
        else:
            new_record = AvalancheForecast(
                zone_id=zone_id,
                zone_name=zone_name,
                forecast_date=forecast_date,
                danger_rating=danger_rating,
                danger_level_text=danger_level_text,
                no_forecast=0,
                fetched_at=datetime.utcnow(),
                product_type=zone_forecast.get('product_type')
            )
            session.add(new_record)

        session.commit()
        logger.info(f"Stored avalanche forecast: zone {zone_id} ({zone_name}), {forecast_date}, danger={danger_level_text}")

        return {
            'danger_rating': danger_rating,
            'danger_level_text': danger_level_text,
            'zone_name': zone_name,
            'no_forecast': False
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching avalanche forecast: {e}")
        # Return cached data if available, even if stale
        if cached:
            return {
                'danger_rating': cached.danger_rating,
                'danger_level_text': cached.danger_level_text,
                'zone_name': cached.zone_name,
                'no_forecast': bool(cached.no_forecast)
            }
        return {
            'danger_rating': None,
            'danger_level_text': 'Error',
            'zone_name': f"Zone {zone_id}",
            'no_forecast': True
        }
    except Exception as e:
        logger.error(f"Unexpected error fetching avalanche forecast: {e}")
        if cached:
            return {
                'danger_rating': cached.danger_rating,
                'danger_level_text': cached.danger_level_text,
                'zone_name': cached.zone_name,
                'no_forecast': bool(cached.no_forecast)
            }
        return {
            'danger_rating': None,
            'danger_level_text': 'Error',
            'zone_name': f"Zone {zone_id}",
            'no_forecast': True
        }
    finally:
        session.close()


# ============================================================================
# Ice Climbing Assessment Functions
# ============================================================================

def calculate_ice_climbing_score(temp, forecast_text, wind_speed):
    """
    Calculate an overall ice climbing score (0-100).

    Args:
        temp: Temperature in Fahrenheit
        forecast_text: Short forecast description
        wind_speed: Wind speed in mph

    Returns:
        int: Score from 0-100 (higher is better)
    """
    score = 0

    # Temperature score (40 points max)
    # Ice climbing is best when cold
    if temp <= 20:
        score += 40
    elif temp <= 32:
        score += 30
    elif temp <= 40:
        score += 15
    else:
        score += max(0, 10 - (temp - 40))

    # Precipitation/conditions score (40 points max)
    forecast_lower = forecast_text.lower()
    if 'snow' in forecast_lower and 'rain' not in forecast_lower:
        score += 40  # Snow is great for building ice
    elif 'sunny' in forecast_lower or 'clear' in forecast_lower:
        score += 30  # Clear is good for stable conditions
    elif 'cloudy' in forecast_lower or 'overcast' in forecast_lower:
        score += 25  # Cloudy is neutral
    elif 'snow' in forecast_lower and 'rain' in forecast_lower:
        score += 10  # Mixed is marginal
    elif 'rain' in forecast_lower:
        score += 0  # Rain is bad - melts ice
    else:
        score += 20  # Default neutral

    # Wind score (20 points max)
    # Calm conditions are safer
    if wind_speed <= 5:
        score += 20
    elif wind_speed <= 10:
        score += 15
    elif wind_speed <= 15:
        score += 10
    elif wind_speed <= 20:
        score += 5
    else:
        score += 0

    return min(100, score)


def get_assessment_grade(score):
    """
    Convert score to letter grade.

    Args:
        score: Ice climbing score (0-100)

    Returns:
        str: Letter grade (A+ to F)
    """
    if score >= 90:
        return 'A+'
    elif score >= 85:
        return 'A'
    elif score >= 80:
        return 'A-'
    elif score >= 75:
        return 'B+'
    elif score >= 70:
        return 'B'
    elif score >= 65:
        return 'B-'
    elif score >= 60:
        return 'C+'
    elif score >= 55:
        return 'C'
    elif score >= 50:
        return 'C-'
    elif score >= 45:
        return 'D+'
    elif score >= 40:
        return 'D'
    elif score >= 35:
        return 'D-'
    else:
        return 'F'


def get_assessment_color(grade):
    """Get CSS class for assessment grade."""
    if grade.startswith('A'):
        return 'assessment-excellent'
    elif grade.startswith('B'):
        return 'assessment-good'
    elif grade.startswith('C'):
        return 'assessment-marginal'
    elif grade.startswith('D'):
        return 'assessment-poor'
    else:
        return 'assessment-bad'


# ============================================================================
# Web Application Helper Functions
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


def get_avalanche_color(danger_level_text, danger_rating):
    """Get color class based on avalanche danger level."""
    if danger_level_text in ['N/A', 'No forecast', 'Error']:
        return 'avalanche-none'

    # Use rating if available (more reliable than text)
    if danger_rating is not None:
        if danger_rating == -1 or danger_rating == 0:
            return 'avalanche-none'
        elif danger_rating == 1:
            return 'avalanche-low'
        elif danger_rating == 2:
            return 'avalanche-moderate'
        elif danger_rating == 3:
            return 'avalanche-considerable'
        elif danger_rating == 4:
            return 'avalanche-high'
        elif danger_rating >= 5:
            return 'avalanche-extreme'

    # Fallback to text-based
    danger_lower = danger_level_text.lower()
    if 'low' in danger_lower:
        return 'avalanche-low'
    elif 'moderate' in danger_lower:
        return 'avalanche-moderate'
    elif 'considerable' in danger_lower:
        return 'avalanche-considerable'
    elif 'high' in danger_lower:
        return 'avalanche-high'
    elif 'extreme' in danger_lower:
        return 'avalanche-extreme'
    else:
        return 'avalanche-none'


def calculate_rolling_assessment(period_date, all_night_temps):
    """
    Calculate rolling 5-day assessment for a specific date.

    Args:
        period_date: The datetime to assess
        all_night_temps: List of tuples (date, temp) for all night periods

    Returns:
        dict: Assessment with status, color, and message
    """
    # Ensure we're working with date objects for comparison
    if isinstance(period_date, datetime):
        period_date = period_date.date()

    # Get the 5 days before this period
    cutoff_date = period_date - timedelta(days=5)

    # Filter to temps in the 5-day window before this period
    relevant_temps = [
        temp for date, temp in all_night_temps
        if cutoff_date <= date < period_date
    ]

    if len(relevant_temps) < 3:
        # Not enough data
        return {
            'status': 'unknown',
            'color': 'assessment-neutral',
            'message': 'Insufficient data',
            'temps': []
        }

    # Check if all lows were at or below thresholds
    all_below_20 = all(temp <= 20 for temp in relevant_temps)
    all_below_25 = all(temp <= 25 for temp in relevant_temps)

    if all_below_20:
        return {
            'status': 'excellent',
            'color': 'assessment-excellent',
            'message': f'Past 5 days: all lows ≤20°F (min: {min(relevant_temps)}°F)',
            'temps': relevant_temps
        }
    elif all_below_25:
        return {
            'status': 'good',
            'color': 'assessment-good',
            'message': f'Past 5 days: all lows ≤25°F (min: {min(relevant_temps)}°F)',
            'temps': relevant_temps
        }
    else:
        return {
            'status': 'poor',
            'color': 'assessment-poor',
            'message': f'Past 5 days: lows too warm (min: {min(relevant_temps)}°F, max: {max(relevant_temps)}°F)',
            'temps': relevant_temps
        }


# ============================================================================
# Historical Weather Data Functions
# ============================================================================

def get_nearest_station(location_name):
    """
    Get the nearest weather station for a location using NWS API.

    Args:
        location_name: Name of the location

    Returns:
        str: Station ID, or None if not found
    """
    location = get_location_by_name(location_name)
    if not location:
        logger.warning(f"Location '{location_name}' not found")
        return None

    try:
        # Get gridpoint info
        points_url = f"{BASE_URL}/points/{location['latitude']},{location['longitude']}"
        resp = requests.get(points_url, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()

        grid_id = data['properties']['gridId']
        grid_x = data['properties']['gridX']
        grid_y = data['properties']['gridY']

        # Get stations for this gridpoint
        stations_url = f"{BASE_URL}/gridpoints/{grid_id}/{grid_x},{grid_y}/stations"
        stations_resp = requests.get(stations_url, headers=HEADERS)
        stations_resp.raise_for_status()
        stations_data = stations_resp.json()

        if stations_data.get('features'):
            # Return the first (nearest) station
            station_id = stations_data['features'][0]['properties']['stationIdentifier']
            logger.info(f"Found station {station_id} for {location_name}")
            return station_id

        logger.warning(f"No stations found for {location_name}")
        return None

    except Exception as e:
        logger.error(f"Error getting station for {location_name}: {e}")
        return None


def get_historical_observations(station_id, start_date=None, end_date=None):
    """
    Fetch historical observations from a weather station using NWS API.

    NOTE: The NWS API only provides observations from the last 6-7 days.
    For older historical data, you would need to use the NCEI CDO API.

    Args:
        station_id: Weather station identifier (e.g., 'TALPE')
        start_date: datetime object for start of range (optional)
        end_date: datetime object for end of range (optional)

    Returns:
        list: List of observation dicts with 'timestamp' and 'temperature' keys
    """
    try:
        obs_url = f"{BASE_URL}/stations/{station_id}/observations"
        logger.info(f"Fetching observations from {station_id}")

        resp = requests.get(obs_url, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()

        observations = []
        for obs_feature in data.get('features', []):
            props = obs_feature['properties']

            # Parse timestamp
            timestamp_str = props.get('timestamp')
            if not timestamp_str:
                continue

            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

            # Filter by date range if specified
            if start_date and timestamp < start_date:
                continue
            if end_date and timestamp > end_date:
                continue

            # Get temperature (in Celsius)
            temp_data = props.get('temperature', {})
            temp_c = temp_data.get('value')

            if temp_c is not None:
                # Convert to Fahrenheit
                temp_f = round(temp_c * 9/5 + 32, 1)

                observations.append({
                    'timestamp': timestamp,
                    'temperature': temp_f
                })

        logger.info(f"Retrieved {len(observations)} observations from {station_id}")
        return observations

    except Exception as e:
        logger.error(f"Error fetching observations from {station_id}: {e}")
        return []


def extract_night_temps(observations, apply_corrections=True, location_name=None):
    """
    Extract nighttime temperatures from observations.
    Nighttime is defined as 6 PM to 6 AM.

    Args:
        observations: List of observation dicts from get_historical_observations
        apply_corrections: Whether to apply elevation corrections
        location_name: Location name for elevation correction lookup

    Returns:
        dict: Dict mapping date to minimum nighttime temperature for that night
    """
    night_temps = {}

    for obs in observations:
        timestamp = obs['timestamp']
        temp = obs['temperature']
        hour = timestamp.hour

        # Nighttime: 6 PM (18:00) to 6 AM (6:00)
        is_night = hour >= 18 or hour < 6

        if is_night:
            # Apply elevation correction if enabled
            if apply_corrections and location_name:
                correction = apply_elevation_correction(temp, location_name)
                temp = correction['corrected_temp']

            # Use the date of the night (if after midnight, still belongs to previous night)
            if hour < 6:
                # Early morning (12 AM - 6 AM) belongs to previous day's night
                night_date = (timestamp.date() - timedelta(days=1))
            else:
                # Evening (6 PM - 11:59 PM)
                night_date = timestamp.date()

            # Track minimum temp for each night
            if night_date not in night_temps:
                night_temps[night_date] = temp
            else:
                night_temps[night_date] = min(night_temps[night_date], temp)

    return night_temps


def get_historical_ice_climbing_assessment(location_name, target_date):
    """
    Calculate the ice climbing assessment for a specific historical date.

    This function:
    1. Finds the nearest weather station for the location
    2. Fetches observations from the NWS API (last 6-7 days available)
    3. Extracts nighttime low temperatures (6 PM - 6 AM)
    4. Applies elevation corrections
    5. Calculates the 5-day rolling assessment for the target date

    NOTE: The NWS API only provides observations from the last 6-7 days.
    For historical data older than 7 days, you would need to:
    - Use the NCEI Climate Data Online (CDO) API at https://www.ncei.noaa.gov/cdo-web/api/v2/
    - Request an API token from NCEI
    - Use their 'data' endpoint with dataset='GHCND' and datatype='TMIN'

    Args:
        location_name: Name of the ice climbing location
        target_date: datetime or date object for the date to assess

    Returns:
        dict: Assessment with keys:
            - status: 'excellent', 'good', 'poor', or 'unknown'
            - color: CSS class for display
            - message: Human-readable description
            - temps: List of night temperatures used in calculation
            - data_source: 'NWS_API' or error message
            - station_id: Weather station used
            - date_range: Tuple of (oldest_date, newest_date) in data
    """
    # Convert to date if datetime
    if isinstance(target_date, datetime):
        target_date = target_date.date()

    # Find nearest station
    station_id = get_nearest_station(location_name)
    if not station_id:
        return {
            'status': 'unknown',
            'color': 'assessment-neutral',
            'message': 'No weather station found',
            'temps': [],
            'data_source': 'ERROR: No station found',
            'station_id': None,
            'date_range': (None, None)
        }

    # Fetch observations
    # NWS API has ~7 days, so fetch all and filter
    observations = get_historical_observations(station_id)

    if not observations:
        return {
            'status': 'unknown',
            'color': 'assessment-neutral',
            'message': 'No observations available',
            'temps': [],
            'data_source': 'ERROR: No observations',
            'station_id': station_id,
            'date_range': (None, None)
        }

    # Extract nighttime temperatures with elevation corrections
    night_temps_dict = extract_night_temps(observations, apply_corrections=True, location_name=location_name)

    # Convert to list of tuples for calculate_rolling_assessment
    night_temps_list = [(date, temp) for date, temp in sorted(night_temps_dict.items())]

    if not night_temps_list:
        return {
            'status': 'unknown',
            'color': 'assessment-neutral',
            'message': 'No nighttime temperatures found',
            'temps': [],
            'data_source': 'NWS_API',
            'station_id': station_id,
            'date_range': (None, None)
        }

    # Check if target date is within available data range
    oldest_date = night_temps_list[0][0]
    newest_date = night_temps_list[-1][0]

    if target_date > newest_date:
        return {
            'status': 'unknown',
            'color': 'assessment-neutral',
            'message': f'Target date {target_date} is beyond available data (newest: {newest_date})',
            'temps': [],
            'data_source': 'NWS_API',
            'station_id': station_id,
            'date_range': (oldest_date, newest_date)
        }

    if target_date < oldest_date - timedelta(days=5):
        return {
            'status': 'unknown',
            'color': 'assessment-neutral',
            'message': f'Target date {target_date} requires data older than available (oldest: {oldest_date}). Use NCEI CDO API for historical data >7 days old.',
            'temps': [],
            'data_source': 'ERROR: Data too old for NWS API',
            'station_id': station_id,
            'date_range': (oldest_date, newest_date)
        }

    # Calculate the rolling assessment for the target date
    assessment = calculate_rolling_assessment(target_date, night_temps_list)

    # Add metadata
    assessment['data_source'] = 'NWS_API'
    assessment['station_id'] = station_id
    assessment['date_range'] = (oldest_date, newest_date)

    return assessment


# ============================================================================
# NCEI Climate Data Online (CDO) API Functions
# ============================================================================

def find_ncei_stations(latitude, longitude, radius_miles=30):
    """
    Find GHCND weather stations near a location.

    Args:
        latitude: Latitude of location
        longitude: Longitude of location
        radius_miles: Search radius in miles (default 30)

    Returns:
        list: List of station dicts with id, name, elevation, date range
    """
    if not NCEI_TOKEN:
        logger.warning("NCEI_TOKEN not set. Cannot search for stations.")
        return []

    try:
        # Convert radius to decimal degrees (rough approximation)
        radius_deg = radius_miles / 69.0  # ~69 miles per degree latitude

        extent = f"{latitude-radius_deg},{longitude-radius_deg},{latitude+radius_deg},{longitude+radius_deg}"

        params = {
            'datasetid': 'GHCND',
            'datatypeid': 'TMIN',
            'extent': extent,
            'limit': 100
        }

        headers = {'token': NCEI_TOKEN}
        resp = requests.get(f"{NCEI_BASE_URL}/stations", headers=headers, params=params, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        stations = []

        for station in data.get('results', []):
            stations.append({
                'id': station['id'],
                'name': station.get('name', 'Unknown'),
                'elevation': station.get('elevation'),
                'mindate': station.get('mindate'),
                'maxdate': station.get('maxdate'),
                'datacoverage': station.get('datacoverage', 0)
            })

        logger.info(f"Found {len(stations)} NCEI stations near ({latitude}, {longitude})")
        return stations

    except Exception as e:
        logger.error(f"Error finding NCEI stations: {e}")
        return []


def get_ncei_tmin_data(station_id, start_date, end_date):
    """
    Fetch daily minimum temperature data from NCEI CDO API.

    Args:
        station_id: GHCND station ID (e.g., 'GHCND:USC00454174')
        start_date: Start date (date object or YYYY-MM-DD string)
        end_date: End date (date object or YYYY-MM-DD string)

    Returns:
        dict: Mapping of date to minimum temperature (°F)
    """
    if not NCEI_TOKEN:
        logger.warning("NCEI_TOKEN not set. Cannot fetch NCEI data.")
        return {}

    try:
        # Convert dates to strings if needed
        if isinstance(start_date, date):
            start_date = start_date.isoformat()
        if isinstance(end_date, date):
            end_date = end_date.isoformat()

        params = {
            'datasetid': 'GHCND',
            'stationid': station_id,
            'datatypeid': 'TMIN',
            'startdate': start_date,
            'enddate': end_date,
            'units': 'standard',  # Returns Fahrenheit
            'limit': 1000  # Max per request
        }

        headers = {'token': NCEI_TOKEN}
        resp = requests.get(f"{NCEI_BASE_URL}/data", headers=headers, params=params, timeout=30)
        resp.raise_for_status()

        data = resp.json()
        tmin_data = {}

        for record in data.get('results', []):
            record_date = date.fromisoformat(record['date'][:10])
            tmin_f = record['value']  # Already in Fahrenheit with units='standard'
            tmin_data[record_date] = tmin_f

        logger.info(f"Retrieved {len(tmin_data)} TMIN records from {station_id}")
        return tmin_data

    except Exception as e:
        logger.error(f"Error fetching NCEI TMIN data: {e}")
        return {}


def get_historical_ice_climbing_assessment_extended(location_name, target_date):
    """
    Calculate ice climbing assessment for ANY historical date using NCEI CDO API.

    This function works for dates beyond the 7-day NWS API limit.
    Requires NCEI_TOKEN environment variable to be set.

    Args:
        location_name: Name of the ice climbing location
        target_date: datetime or date object for the date to assess

    Returns:
        dict: Assessment with same format as get_historical_ice_climbing_assessment
    """
    # Convert to date if datetime
    if isinstance(target_date, datetime):
        target_date = target_date.date()

    # First try NWS API for recent dates (< 7 days old)
    days_old = (date.today() - target_date).days
    if days_old < 7:
        logger.info(f"Using NWS API for recent date: {target_date}")
        return get_historical_ice_climbing_assessment(location_name, target_date)

    # For older dates, use NCEI CDO API
    if not NCEI_TOKEN:
        return {
            'status': 'unknown',
            'color': 'assessment-neutral',
            'message': 'NCEI_TOKEN not set. Export NCEI_TOKEN environment variable or get token from https://www.ncdc.noaa.gov/cdo-web/token',
            'temps': [],
            'data_source': 'ERROR: No NCEI token',
            'station_id': None,
            'date_range': (None, None)
        }

    location = get_location_by_name(location_name)
    if not location:
        return {
            'status': 'unknown',
            'color': 'assessment-neutral',
            'message': f'Location "{location_name}" not found',
            'temps': [],
            'data_source': 'ERROR: Location not found',
            'station_id': None,
            'date_range': (None, None)
        }

    # Find nearest GHCND station
    logger.info(f"Searching for NCEI stations near {location_name}")
    stations = find_ncei_stations(location['latitude'], location['longitude'])

    if not stations:
        return {
            'status': 'unknown',
            'color': 'assessment-neutral',
            'message': 'No NCEI weather stations found nearby',
            'temps': [],
            'data_source': 'ERROR: No NCEI stations',
            'station_id': None,
            'date_range': (None, None)
        }

    # Use the first (nearest/best) station
    station = stations[0]
    station_id = station['id']

    # We need 5 days before the target date for the rolling assessment
    start_date = target_date - timedelta(days=5)
    end_date = target_date

    logger.info(f"Fetching TMIN data from {station_id} for {start_date} to {end_date}")
    tmin_data = get_ncei_tmin_data(station_id, start_date, end_date)

    if not tmin_data:
        return {
            'status': 'unknown',
            'color': 'assessment-neutral',
            'message': f'No temperature data available for {target_date}',
            'temps': [],
            'data_source': 'NCEI_CDO_API',
            'station_id': station_id,
            'date_range': (None, None)
        }

    # Apply elevation corrections to TMIN values
    corrected_temps = {}
    for temp_date, temp in tmin_data.items():
        correction = apply_elevation_correction(temp, location_name)
        corrected_temps[temp_date] = correction['corrected_temp']

    # Convert to list of tuples for calculate_rolling_assessment
    night_temps_list = [(d, t) for d, t in sorted(corrected_temps.items())]

    if len(night_temps_list) < 3:
        return {
            'status': 'unknown',
            'color': 'assessment-neutral',
            'message': f'Insufficient data (only {len(night_temps_list)} days)',
            'temps': [],
            'data_source': 'NCEI_CDO_API',
            'station_id': station_id,
            'date_range': (night_temps_list[0][0] if night_temps_list else None,
                          night_temps_list[-1][0] if night_temps_list else None)
        }

    # Calculate the rolling assessment
    assessment = calculate_rolling_assessment(target_date, night_temps_list)

    # Add metadata
    assessment['data_source'] = 'NCEI_CDO_API'
    assessment['station_id'] = station_id
    assessment['station_name'] = station['name']
    assessment['date_range'] = (night_temps_list[0][0], night_temps_list[-1][0])

    return assessment


def get_location_data(location_name, days=7):
    """
    Get both historical and future forecast data for a specific location.
    Each period gets a rolling 5-day assessment based on night temps.

    Args:
        location_name: Name of the location
        days: Number of days of historical data to retrieve

    Returns:
        list: Combined historical and future data with rolling assessments
    """
    session = get_session(DATABASE_URL)

    # Get avalanche zone for this location
    location = get_location_by_name(location_name)
    avalanche_zone_id = location.get('nwac_zone_id') if location else None

    try:
        # Get enough data for context (need more than display window for rolling assessment)
        cutoff_time = datetime.utcnow() - timedelta(days=days+10)
        all_periods = []

        # First, get ALL night temperatures for rolling assessment
        # We need both historical and future night temps

        # Get historical nights (backfilled data)
        historical_cutoff = datetime.utcnow() - timedelta(days=1)
        historical_nights = session.query(WeatherForecast).filter(
            and_(
                WeatherForecast.location_name == location_name,
                WeatherForecast.fetched_at >= cutoff_time,
                WeatherForecast.fetched_at < historical_cutoff,
                WeatherForecast.period_name.contains('Night')
            )
        ).order_by(WeatherForecast.fetched_at).all()

        # Build night temp map from historical data
        night_temp_map = {}
        for forecast in historical_nights:
            # For historical data, fetched_at IS the period date
            date_key = forecast.fetched_at.date()
            if date_key not in night_temp_map or forecast.fetched_at > night_temp_map[date_key][0]:
                # Apply elevation correction to night temperature for rolling assessment
                elev_correction = apply_elevation_correction(forecast.temperature, location_name)
                night_temp_map[date_key] = (forecast.fetched_at, elev_correction['corrected_temp'])

        # Get forecast nights (most recent fetch)
        latest_fetch = session.query(func.max(WeatherForecast.fetched_at)).filter(
            WeatherForecast.location_name == location_name
        ).scalar()

        if latest_fetch:
            forecast_nights = session.query(WeatherForecast).filter(
                and_(
                    WeatherForecast.location_name == location_name,
                    WeatherForecast.fetched_at == latest_fetch,
                    WeatherForecast.period_name.contains('Night')
                )
            ).order_by(WeatherForecast.id).all()

            # For forecast data, estimate dates based on position
            current_date = datetime.utcnow().date()
            for i, forecast in enumerate(forecast_nights):
                # Each period is roughly 12 hours, so each night is about i days out
                # First night (Tonight) is today, next is tomorrow, etc.
                est_date = current_date + timedelta(days=i)
                if est_date not in night_temp_map:
                    # Apply elevation correction to night temperature for rolling assessment
                    elev_correction = apply_elevation_correction(forecast.temperature, location_name)
                    night_temp_map[est_date] = (forecast.fetched_at, elev_correction['corrected_temp'])

        # Convert to sorted list of (date, temp)
        all_night_temps = [(date, temp) for date, (_, temp) in sorted(night_temp_map.items())]

        # Now get historical data for display (one fetch per day)
        # Exclude today's fetches - only show previous days in historical section
        # Get the LATEST fetch for each day to avoid duplicates
        display_cutoff = datetime.utcnow() - timedelta(days=days)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Subquery to get the max fetched_at per date
        from sqlalchemy import Date, cast
        subquery = session.query(
            cast(WeatherForecast.fetched_at, Date).label('fetch_date'),
            func.max(WeatherForecast.fetched_at).label('max_fetched_at')
        ).filter(
            and_(
                WeatherForecast.location_name == location_name,
                WeatherForecast.fetched_at >= display_cutoff,
                WeatherForecast.fetched_at < today_start
            )
        ).group_by('fetch_date').subquery()

        # Get the actual fetch times
        fetch_times = session.query(subquery.c.max_fetched_at).order_by(subquery.c.max_fetched_at).all()

        for (fetch_time,) in fetch_times:
            # Get the first period from each fetch
            forecast = session.query(WeatherForecast).filter(
                and_(
                    WeatherForecast.location_name == location_name,
                    WeatherForecast.fetched_at == fetch_time
                )
            ).first()

            if forecast:
                wind_speed = parse_wind_speed(forecast.wind_speed)

                # Apply elevation correction to temperature
                elev_correction = apply_elevation_correction(forecast.temperature, location_name)

                # Calculate rolling 5-day assessment (already using corrected night temps)
                period_datetime = datetime.combine(fetch_time.date(), datetime.min.time())
                rolling_assessment = calculate_rolling_assessment(period_datetime, all_night_temps)

                # Fetch avalanche forecast for this date
                avalanche_data = fetch_avalanche_forecast(avalanche_zone_id, fetch_time.date())

                all_periods.append({
                    'is_historical': True,
                    'date': fetch_time.strftime('%a %m/%d'),
                    'period_name': forecast.period_name,
                    'temperature': elev_correction['corrected_temp'],
                    'temperature_original': elev_correction['original_temp'],
                    'elevation_corrected': elev_correction['has_correction'],
                    'elevation_diff': elev_correction['elevation_diff'],
                    'correction_applied': elev_correction['correction_applied'],
                    'temp_color': get_temp_color(elev_correction['corrected_temp']),
                    'wind_speed': wind_speed,
                    'wind_speed_str': forecast.wind_speed,
                    'wind_color': get_wind_color(wind_speed),
                    'short_forecast': forecast.short_forecast,
                    'forecast_color': get_forecast_color(forecast.short_forecast),
                    'detailed_forecast': forecast.detailed_forecast,
                    'rolling_assessment': rolling_assessment['status'],
                    'rolling_assessment_color': rolling_assessment['color'],
                    'rolling_assessment_message': rolling_assessment['message'],
                    'avalanche_danger': avalanche_data['danger_level_text'],
                    'avalanche_rating': avalanche_data['danger_rating'],
                    'avalanche_color': get_avalanche_color(avalanche_data['danger_level_text'], avalanche_data['danger_rating'])
                })

        # Get future forecast (latest fetch)
        latest_fetch = session.query(func.max(WeatherForecast.fetched_at)).filter(
            WeatherForecast.location_name == location_name
        ).scalar()

        if latest_fetch:
            forecasts = session.query(WeatherForecast).filter(
                and_(
                    WeatherForecast.location_name == location_name,
                    WeatherForecast.fetched_at == latest_fetch
                )
            ).order_by(WeatherForecast.id).all()

            # For future periods, we need to estimate dates
            # Start from today (date only, not datetime) and add days for each period
            current_date_only = datetime.utcnow().date()
            base_datetime = datetime.combine(current_date_only, datetime.min.time())

            # Process each future period
            for i, forecast in enumerate(forecasts):
                wind_speed = parse_wind_speed(forecast.wind_speed)

                # Apply elevation correction to temperature
                elev_correction = apply_elevation_correction(forecast.temperature, location_name)

                # Estimate the date for this period (roughly i*0.5 days out)
                # Each period is ~12 hours, so period 0 is today, period 2 is tomorrow, etc.
                est_datetime = base_datetime + timedelta(days=i*0.5)

                # Calculate rolling 5-day assessment (already using corrected night temps)
                rolling_assessment = calculate_rolling_assessment(est_datetime, all_night_temps)

                # Format the date for display
                formatted_date = est_datetime.strftime('%a %m/%d')

                # Fetch avalanche forecast for this date
                avalanche_data = fetch_avalanche_forecast(avalanche_zone_id, est_datetime.date())

                all_periods.append({
                    'is_historical': False,
                    'date': formatted_date,
                    'period_name': forecast.period_name,
                    'temperature': elev_correction['corrected_temp'],
                    'temperature_original': elev_correction['original_temp'],
                    'elevation_corrected': elev_correction['has_correction'],
                    'elevation_diff': elev_correction['elevation_diff'],
                    'correction_applied': elev_correction['correction_applied'],
                    'temp_color': get_temp_color(elev_correction['corrected_temp']),
                    'wind_speed': wind_speed,
                    'wind_speed_str': forecast.wind_speed,
                    'wind_color': get_wind_color(wind_speed),
                    'short_forecast': forecast.short_forecast,
                    'forecast_color': get_forecast_color(forecast.short_forecast),
                    'detailed_forecast': forecast.detailed_forecast,
                    'rolling_assessment': rolling_assessment['status'],
                    'rolling_assessment_color': rolling_assessment['color'],
                    'rolling_assessment_message': rolling_assessment['message'],
                    'avalanche_danger': avalanche_data['danger_level_text'],
                    'avalanche_rating': avalanche_data['danger_rating'],
                    'avalanche_color': get_avalanche_color(avalanche_data['danger_level_text'], avalanche_data['danger_rating'])
                })

        return all_periods

    finally:
        session.close()


@app.route('/')
def index():
    """Main page showing weather conditions for all ice climbing locations."""
    locations = get_all_locations()

    # Get data for each location
    locations_data = []
    for location in locations:
        periods = get_location_data(location['name'], days=7)

        if periods:  # Only include if we have data
            locations_data.append({
                'name': location['name'],
                'description': location['description'],
                'links': location.get('links', []),
                'periods': periods
            })

    return render_template('index.html', locations=locations_data)


@app.route('/json')
def index_json():
    """JSON API endpoint returning all weather data and assessments."""
    from flask import jsonify

    locations = get_all_locations()

    # Get data for each location
    locations_data = []
    for location in locations:
        periods = get_location_data(location['name'], days=7)

        if periods:  # Only include if we have data
            locations_data.append({
                'name': location['name'],
                'description': location['description'],
                'latitude': location['latitude'],
                'longitude': location['longitude'],
                'periods': periods
            })

    return jsonify({
        'locations': locations_data,
        'generated_at': datetime.utcnow().isoformat(),
        'total_locations': len(locations_data)
    })


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point that starts both the collector and web server."""
    logger.info("="*70)
    logger.info("STARTING TOO WARM - Ice Climbing Weather Monitor")
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
    # Use environment variable for port, default to 5001 (5000 often conflicts with other services)
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"Starting Flask web server on http://0.0.0.0:{port}")
    logger.info("="*70)
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=True)


if __name__ == '__main__':
    main()
