#!/usr/bin/env python3
"""
Simple example of using the historical ice climbing assessment function.

This demonstrates the basic usage pattern for getting historical assessments.
"""

from app import get_historical_ice_climbing_assessment
from datetime import datetime, timedelta

# Example 1: Get assessment for yesterday
print("Example 1: Yesterday's Assessment")
print("-" * 50)

yesterday = datetime.now().date() - timedelta(days=1)
result = get_historical_ice_climbing_assessment('Franklin Falls', yesterday)

print(f"Date: {yesterday}")
print(f"Status: {result['status']}")
print(f"Message: {result['message']}")
print()

# Example 2: Check multiple dates
print("Example 2: Last 5 Days")
print("-" * 50)

location = 'Leavenworth'
for days_ago in range(1, 6):
    date = datetime.now().date() - timedelta(days=days_ago)
    result = get_historical_ice_climbing_assessment(location, date)
    status_symbol = {
        'excellent': '✓✓✓',
        'good': '✓✓',
        'poor': '✗',
        'unknown': '?'
    }.get(result['status'], '?')

    print(f"{date}: {status_symbol} {result['status'].upper()}")

print()

# Example 3: Detailed assessment with all info
print("Example 3: Detailed Assessment")
print("-" * 50)

target_date = datetime.now().date() - timedelta(days=2)
result = get_historical_ice_climbing_assessment('Alpental', target_date)

print(f"Location: Alpental")
print(f"Target Date: {target_date}")
print(f"Weather Station: {result['station_id']}")
print(f"Assessment: {result['status'].upper()}")
print(f"Temperature Range: {min(result['temps']) if result['temps'] else 'N/A'}°F - {max(result['temps']) if result['temps'] else 'N/A'}°F")
print(f"Data Coverage: {result['date_range'][0]} to {result['date_range'][1]}")
print()

# Example 4: Error handling - date too old
print("Example 4: Handling Old Dates (Beyond NWS API Coverage)")
print("-" * 50)

old_date = datetime.now().date() - timedelta(days=30)
result = get_historical_ice_climbing_assessment('Franklin Falls', old_date)

print(f"Trying to get assessment for: {old_date}")
print(f"Status: {result['status']}")
print(f"Message: {result['message']}")
print()
print("Note: For dates older than 7 days, use NCEI CDO API instead.")
print("See documentation in get_historical_ice_climbing_assessment() function.")
