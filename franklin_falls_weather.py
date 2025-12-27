#!/usr/bin/env python3
"""
Script to retrieve weather forecast for Franklin Falls, Washington
using the National Weather Service API.
"""

import requests
import json

# Franklin Falls, Washington coordinates
LATITUDE = 47.4254
LONGITUDE = -121.4320

# API endpoints
BASE_URL = "https://api.weather.gov"

# User-Agent header is required by NWS API
HEADERS = {
    "User-Agent": "(Franklin Falls Weather Script, weather@example.com)"
}

def get_weather_forecast():
    """Get weather forecast for Franklin Falls, Washington."""

    # Step 1: Get grid point information
    print(f"Getting weather information for Franklin Falls, WA")
    print(f"Coordinates: {LATITUDE}, {LONGITUDE}\n")

    points_url = f"{BASE_URL}/points/{LATITUDE},{LONGITUDE}"
    print(f"Requesting grid point data from: {points_url}")

    try:
        response = requests.get(points_url, headers=HEADERS)
        response.raise_for_status()
        points_data = response.json()

        # Extract forecast URL
        forecast_url = points_data['properties']['forecast']
        print(f"Forecast URL: {forecast_url}\n")

        # Step 2: Get the actual forecast
        print("Fetching forecast...")
        forecast_response = requests.get(forecast_url, headers=HEADERS)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        # Print the forecast
        print("=" * 70)
        print("WEATHER FORECAST FOR FRANKLIN FALLS, WASHINGTON")
        print("=" * 70)

        periods = forecast_data['properties']['periods']

        for period in periods:
            print(f"\n{period['name']}:")
            print(f"  Temperature: {period['temperature']}°{period['temperatureUnit']}")
            print(f"  Wind: {period['windSpeed']} {period['windDirection']}")
            print(f"  Forecast: {period['shortForecast']}")
            print(f"  Details: {period['detailedForecast']}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return False
    except KeyError as e:
        print(f"Error parsing response data: {e}")
        print(f"Response: {json.dumps(points_data if 'points_data' in locals() else forecast_data, indent=2)}")
        return False

    return True

if __name__ == "__main__":
    get_weather_forecast()
