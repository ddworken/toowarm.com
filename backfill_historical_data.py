#!/usr/bin/env python3
"""
Script to backfill historical weather data for testing purposes.
Generates realistic weather data for the past 5 days for all locations.
"""

from datetime import datetime, timedelta
from models import WeatherForecast, init_db
from locations import get_all_locations
import random

DATABASE_URL = 'sqlite:///ice_climbing_weather.db'

# Realistic winter temperature ranges for each location (highs and lows)
LOCATION_TEMPS = {
    'Franklin Falls': {'high': (35, 50), 'low': (18, 32)},
    'Exit 38': {'high': (38, 52), 'low': (20, 35)},
    'Alpental': {'high': (35, 48), 'low': (18, 30)},
    'Leavenworth': {'high': (30, 45), 'low': (15, 28)},
    'White Pine': {'high': (28, 42), 'low': (12, 25)},
    'Banks Lake': {'high': (32, 48), 'low': (18, 30)}
}

WEATHER_CONDITIONS = [
    ('Mostly Sunny', 'Mostly sunny with light clouds.'),
    ('Partly Cloudy', 'Partly cloudy skies throughout the day.'),
    ('Light Snow', 'Light snow showers. New snow accumulation of less than one inch.'),
    ('Snow', 'Snow. New snow accumulation of 1 to 3 inches possible.'),
    ('Light Rain', 'Light rain showers. Little or no precipitation accumulation.'),
    ('Rain And Snow', 'Rain and snow mix. New snow accumulation of less than one inch.'),
    ('Cloudy', 'Cloudy skies throughout the day.'),
    ('Mostly Clear', 'Mostly clear skies with few clouds.')
]

def generate_weather_data_for_day(location, date, is_night=False):
    """Generate realistic weather data for a specific day."""
    location_name = location['name']
    temp_range = LOCATION_TEMPS[location_name]

    if is_night:
        temp = random.randint(*temp_range['low'])
        period_name = f"{date.strftime('%A')} Night"
    else:
        temp = random.randint(*temp_range['high'])
        period_name = date.strftime('%A')

    # Select weather condition (favor snow/clear in cold temps)
    if temp < 25:
        conditions = [
            ('Light Snow', 'Light snow showers. New snow accumulation of less than one inch.'),
            ('Snow', 'Snow. New snow accumulation of 1 to 3 inches possible.'),
            ('Mostly Clear', 'Mostly clear and cold.'),
            ('Partly Cloudy', 'Partly cloudy and cold.')
        ]
    elif temp < 35:
        conditions = [
            ('Light Snow', 'Light snow showers. New snow accumulation of less than one inch.'),
            ('Rain And Snow', 'Rain and snow mix.'),
            ('Cloudy', 'Cloudy and cool.'),
            ('Partly Cloudy', 'Partly cloudy.')
        ]
    else:
        conditions = WEATHER_CONDITIONS

    short_forecast, detailed_forecast = random.choice(conditions)

    # Generate wind
    wind_speed_num = random.randint(2, 15)
    wind_direction = random.choice(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
    wind_speed = f"{wind_speed_num} mph {wind_direction}"

    return {
        'period_name': period_name,
        'temperature': temp,
        'wind_speed': wind_speed,
        'wind_direction': wind_direction,
        'short_forecast': short_forecast,
        'detailed_forecast': detailed_forecast
    }


def backfill_data(days=5):
    """Backfill historical weather data for the past N days."""
    print("="*70)
    print("BACKFILLING HISTORICAL WEATHER DATA")
    print("="*70)

    # Initialize database
    _, SessionLocal = init_db(DATABASE_URL)
    session = SessionLocal()

    try:
        locations = get_all_locations()

        # For each day in the past
        for days_ago in range(days, 0, -1):
            date = datetime.utcnow() - timedelta(days=days_ago)

            print(f"\nGenerating data for {date.strftime('%Y-%m-%d (%A)')}")

            for location in locations:
                # Generate daytime and nighttime data
                for is_night in [False, True]:
                    weather_data = generate_weather_data_for_day(location, date, is_night)

                    # Adjust fetched_at time for night vs day
                    if is_night:
                        fetched_at = date.replace(hour=18, minute=0, second=0, microsecond=0)
                    else:
                        fetched_at = date.replace(hour=12, minute=0, second=0, microsecond=0)

                    record = WeatherForecast(
                        location_name=location['name'],
                        latitude=location['latitude'],
                        longitude=location['longitude'],
                        fetched_at=fetched_at,
                        period_name=weather_data['period_name'],
                        temperature=weather_data['temperature'],
                        temperature_unit='F',
                        wind_speed=weather_data['wind_speed'],
                        wind_direction=weather_data['wind_direction'],
                        short_forecast=weather_data['short_forecast'],
                        detailed_forecast=weather_data['detailed_forecast'],
                        grid_id='TEST',
                        grid_x=0,
                        grid_y=0
                    )

                    session.add(record)

                print(f"  ✓ {location['name']}")

        session.commit()
        print(f"\n{'='*70}")
        print(f"Successfully backfilled {days} days of data for {len(locations)} locations")
        print(f"Total records added: {days * len(locations) * 2} (day + night for each)")
        print(f"{'='*70}")

    except Exception as e:
        session.rollback()
        print(f"Error backfilling data: {e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    import sys

    days = 5
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print("Usage: python backfill_historical_data.py [days]")
            sys.exit(1)

    backfill_data(days)
