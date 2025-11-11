#!/usr/bin/env python3
"""
Utility script to view historical weather data from the database.
"""

import sys
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from models import WeatherForecast, get_session

DATABASE_URL = 'sqlite:///franklin_falls_weather.db'


def view_latest_forecast():
    """Display the most recent weather forecast."""
    session = get_session(DATABASE_URL)

    try:
        # Get the latest fetch time
        latest_fetch = session.query(func.max(WeatherForecast.fetched_at)).scalar()

        if not latest_fetch:
            print("No weather data found in database.")
            return

        print("="*70)
        print("LATEST WEATHER FORECAST FOR FRANKLIN FALLS, WASHINGTON")
        print("="*70)
        print(f"Fetched at: {latest_fetch}")
        print()

        # Get all periods from the latest fetch
        forecasts = session.query(WeatherForecast).filter(
            WeatherForecast.fetched_at == latest_fetch
        ).all()

        for forecast in forecasts:
            print(f"{forecast.period_name}:")
            print(f"  Temperature: {forecast.temperature}°{forecast.temperature_unit}")
            print(f"  Wind: {forecast.wind_speed} {forecast.wind_direction}")
            print(f"  Forecast: {forecast.short_forecast}")
            print(f"  Details: {forecast.detailed_forecast}")
            print()

    finally:
        session.close()


def view_fetch_history(limit=10):
    """Display history of data fetches."""
    session = get_session(DATABASE_URL)

    try:
        # Get distinct fetch times
        fetch_times = session.query(
            WeatherForecast.fetched_at,
            func.count(WeatherForecast.id).label('period_count')
        ).group_by(
            WeatherForecast.fetched_at
        ).order_by(
            desc(WeatherForecast.fetched_at)
        ).limit(limit).all()

        if not fetch_times:
            print("No weather data found in database.")
            return

        print("="*70)
        print(f"FETCH HISTORY (Last {limit} fetches)")
        print("="*70)

        for fetch_time, period_count in fetch_times:
            # Get a sample forecast from this fetch
            sample = session.query(WeatherForecast).filter(
                WeatherForecast.fetched_at == fetch_time
            ).first()

            print(f"\nFetch time: {fetch_time}")
            print(f"  Periods stored: {period_count}")
            print(f"  Sample: {sample.period_name} - {sample.temperature}°{sample.temperature_unit}, {sample.short_forecast}")

    finally:
        session.close()


def view_temperature_trends(hours=24):
    """Display temperature trends over time."""
    session = get_session(DATABASE_URL)

    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Get forecasts for "This Afternoon", "Tonight", "Today", etc.
        forecasts = session.query(WeatherForecast).filter(
            WeatherForecast.fetched_at >= cutoff_time,
            WeatherForecast.period_name.in_(['This Afternoon', 'Tonight', 'Today', 'Veterans Day'])
        ).order_by(
            WeatherForecast.fetched_at
        ).all()

        if not forecasts:
            print(f"No data found in the last {hours} hours.")
            return

        print("="*70)
        print(f"TEMPERATURE TRENDS (Last {hours} hours)")
        print("="*70)

        for forecast in forecasts:
            print(f"{forecast.fetched_at.strftime('%Y-%m-%d %H:%M')} | "
                  f"{forecast.period_name:20s} | "
                  f"{forecast.temperature:3d}°{forecast.temperature_unit} | "
                  f"{forecast.short_forecast}")

    finally:
        session.close()


def view_statistics():
    """Display database statistics."""
    session = get_session(DATABASE_URL)

    try:
        total_records = session.query(func.count(WeatherForecast.id)).scalar()
        total_fetches = session.query(func.count(func.distinct(WeatherForecast.fetched_at))).scalar()
        first_fetch = session.query(func.min(WeatherForecast.fetched_at)).scalar()
        last_fetch = session.query(func.max(WeatherForecast.fetched_at)).scalar()

        print("="*70)
        print("DATABASE STATISTICS")
        print("="*70)
        print(f"Total records: {total_records}")
        print(f"Total fetches: {total_fetches}")
        print(f"First fetch: {first_fetch}")
        print(f"Last fetch: {last_fetch}")

        if first_fetch and last_fetch:
            duration = last_fetch - first_fetch
            print(f"Data collection duration: {duration}")

    finally:
        session.close()


def main():
    """Main function to handle command-line arguments."""
    if len(sys.argv) < 2:
        print("Franklin Falls Weather History Viewer")
        print("\nUsage:")
        print("  python view_weather_history.py latest    - View latest forecast")
        print("  python view_weather_history.py history   - View fetch history")
        print("  python view_weather_history.py trends    - View temperature trends")
        print("  python view_weather_history.py stats     - View database statistics")
        return

    command = sys.argv[1].lower()

    if command == 'latest':
        view_latest_forecast()
    elif command == 'history':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        view_fetch_history(limit)
    elif command == 'trends':
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        view_temperature_trends(hours)
    elif command == 'stats':
        view_statistics()
    else:
        print(f"Unknown command: {command}")
        print("Use: latest, history, trends, or stats")


if __name__ == "__main__":
    main()
