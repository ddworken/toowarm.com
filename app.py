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
from sqlalchemy import func, and_
from models import WeatherForecast, get_session, init_db
from locations import get_all_locations
import requests
import re

# Configuration
BASE_URL = "https://api.weather.gov"
HEADERS = {"User-Agent": "(Too Warm Ice Climbing Weather, weather@example.com)"}
FETCH_INTERVAL = 3600  # 1 hour
DATABASE_URL = 'sqlite:///ice_climbing_weather.db'

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
                night_temp_map[date_key] = (forecast.fetched_at, forecast.temperature)

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
                    night_temp_map[est_date] = (forecast.fetched_at, forecast.temperature)

        # Convert to sorted list of (date, temp)
        all_night_temps = [(date, temp) for date, (_, temp) in sorted(night_temp_map.items())]

        # Now get historical data for display (distinct fetch times)
        display_cutoff = datetime.utcnow() - timedelta(days=days)
        fetch_times = session.query(WeatherForecast.fetched_at).filter(
            and_(
                WeatherForecast.location_name == location_name,
                WeatherForecast.fetched_at >= display_cutoff
            )
        ).distinct().order_by(WeatherForecast.fetched_at).all()

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

                # Calculate rolling 5-day assessment
                period_datetime = datetime.combine(fetch_time.date(), datetime.min.time())
                rolling_assessment = calculate_rolling_assessment(period_datetime, all_night_temps)

                all_periods.append({
                    'is_historical': True,
                    'date': fetch_time.strftime('%a %m/%d'),
                    'period_name': forecast.period_name,
                    'temperature': forecast.temperature,
                    'temp_color': get_temp_color(forecast.temperature),
                    'wind_speed': wind_speed,
                    'wind_speed_str': forecast.wind_speed,
                    'wind_color': get_wind_color(wind_speed),
                    'short_forecast': forecast.short_forecast,
                    'forecast_color': get_forecast_color(forecast.short_forecast),
                    'detailed_forecast': forecast.detailed_forecast,
                    'rolling_assessment': rolling_assessment['status'],
                    'rolling_assessment_color': rolling_assessment['color'],
                    'rolling_assessment_message': rolling_assessment['message']
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

                # Estimate the date for this period (roughly i*0.5 days out)
                # Each period is ~12 hours, so period 0 is today, period 2 is tomorrow, etc.
                est_datetime = base_datetime + timedelta(days=i*0.5)

                # Calculate rolling 5-day assessment
                rolling_assessment = calculate_rolling_assessment(est_datetime, all_night_temps)

                all_periods.append({
                    'is_historical': False,
                    'date': '',
                    'period_name': forecast.period_name,
                    'temperature': forecast.temperature,
                    'temp_color': get_temp_color(forecast.temperature),
                    'wind_speed': wind_speed,
                    'wind_speed_str': forecast.wind_speed,
                    'wind_color': get_wind_color(wind_speed),
                    'short_forecast': forecast.short_forecast,
                    'forecast_color': get_forecast_color(forecast.short_forecast),
                    'detailed_forecast': forecast.detailed_forecast,
                    'rolling_assessment': rolling_assessment['status'],
                    'rolling_assessment_color': rolling_assessment['color'],
                    'rolling_assessment_message': rolling_assessment['message']
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
    logger.info("Starting Flask web server on http://0.0.0.0:5000")
    logger.info("="*70)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
