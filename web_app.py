#!/usr/bin/env python3
"""
Flask web application to display Franklin Falls ice climbing weather conditions.
Similar to toorainy.com but focused on ice climbing conditions.
"""

from flask import Flask, render_template
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from models import WeatherForecast, get_session
import re

app = Flask(__name__)

DATABASE_URL = 'sqlite:///franklin_falls_weather.db'


def parse_temperature(temp, unit):
    """Convert temperature to Fahrenheit if needed."""
    if unit == 'F':
        return temp
    elif unit == 'C':
        return (temp * 9/5) + 32
    return temp


def get_temp_color(temp):
    """
    Get color class based on temperature for ice climbing.
    Cold temps (below freezing) are good for ice climbing.
    """
    if temp <= 20:
        return 'temp-excellent'  # Dark green
    elif temp <= 32:
        return 'temp-good'  # Green
    elif temp <= 40:
        return 'temp-marginal'  # Yellow
    else:
        return 'temp-poor'  # Red


def get_forecast_color(forecast_text):
    """
    Get color class based on forecast conditions.
    Snow is good, rain is bad for ice climbing.
    """
    forecast_lower = forecast_text.lower()

    if 'snow' in forecast_lower and 'rain' not in forecast_lower:
        return 'condition-excellent'  # Snow only
    elif 'snow' in forecast_lower and 'rain' in forecast_lower:
        return 'condition-marginal'  # Mixed
    elif 'rain' in forecast_lower:
        return 'condition-poor'  # Rain
    elif 'sunny' in forecast_lower or 'clear' in forecast_lower:
        return 'condition-good'  # Clear/sunny
    elif 'cloudy' in forecast_lower or 'overcast' in forecast_lower:
        return 'condition-neutral'  # Cloudy
    else:
        return 'condition-neutral'


def parse_wind_speed(wind_str):
    """Extract numeric wind speed from string like '5 to 10 mph'."""
    if not wind_str:
        return 0

    # Try to extract the first number
    match = re.search(r'(\d+)', wind_str)
    if match:
        return int(match.group(1))
    return 0


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
    """
    Get historical weather data for the past N days.
    Returns a list of daily summaries.
    """
    session = get_session(DATABASE_URL)

    try:
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        # Get all distinct fetch times in the past N days
        fetch_times = session.query(WeatherForecast.fetched_at).filter(
            WeatherForecast.fetched_at >= cutoff_time
        ).distinct().order_by(WeatherForecast.fetched_at).all()

        historical_data = []

        for (fetch_time,) in fetch_times:
            # Get the first period from each fetch (usually "Today" or similar)
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


@app.route('/about')
def about():
    """About page explaining the site."""
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
