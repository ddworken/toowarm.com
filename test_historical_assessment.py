#!/usr/bin/env python3
"""
Test script for historical ice climbing assessment functionality.

This demonstrates how to use the NWS API to pull historical weather data
and calculate ice climbing assessments for past dates.

NOTE: The NWS API only provides observations from the last 6-7 days.
For older historical data, you would need to use the NCEI CDO API.
"""

from app import get_historical_ice_climbing_assessment
from datetime import datetime, timedelta

def test_location(location_name, target_date):
    """Test historical assessment for a single location."""
    print(f"\n{'=' * 70}")
    print(f"Location: {location_name}")
    print(f"Target Date: {target_date}")
    print('-' * 70)

    result = get_historical_ice_climbing_assessment(location_name, target_date)

    print(f"Assessment Status: {result['status'].upper()}")
    print(f"Message: {result['message']}")
    print(f"Weather Station: {result['station_id']}")
    print(f"Data Source: {result['data_source']}")
    print(f"Available Data Range: {result['date_range'][0]} to {result['date_range'][1]}")

    if result['temps']:
        print(f"Night Temps Used: {result['temps']}")
        print(f"Min Temp: {min(result['temps'])}°F")
        print(f"Max Temp: {max(result['temps'])}°F")

    # Interpretation
    print("\nInterpretation:")
    if result['status'] == 'excellent':
        print("  ✓✓✓ Excellent conditions - All night lows ≤20°F for past 5 days")
    elif result['status'] == 'good':
        print("  ✓✓ Good conditions - All night lows ≤25°F for past 5 days")
    elif result['status'] == 'poor':
        print("  ✗ Poor conditions - Night temps too warm for good ice formation")
    else:
        print("  ? Unable to assess - Insufficient data")

    return result


def main():
    print("=" * 70)
    print("HISTORICAL ICE CLIMBING ASSESSMENT TEST")
    print("Using NWS API Observations (Last 6-7 Days)")
    print("=" * 70)

    # Test different dates
    today = datetime.now().date()
    dates_to_test = [
        today - timedelta(days=1),  # Yesterday
        today - timedelta(days=3),  # 3 days ago
        today - timedelta(days=5),  # 5 days ago
    ]

    # Test locations
    locations_to_test = [
        'Franklin Falls',
        'Leavenworth',
        'Alpental'
    ]

    # Run tests
    for target_date in dates_to_test:
        for location in locations_to_test:
            test_location(location, target_date)

    # Show limitations
    print(f"\n{'=' * 70}")
    print("IMPORTANT NOTES:")
    print("=" * 70)
    print("1. NWS API only provides ~6-7 days of historical observations")
    print("2. For older data, use the NCEI Climate Data Online (CDO) API:")
    print("   - API Endpoint: https://www.ncei.noaa.gov/cdo-web/api/v2/")
    print("   - Requires free API token")
    print("   - Dataset: GHCND (Global Historical Climatology Network Daily)")
    print("   - Datatype: TMIN (minimum temperature)")
    print("3. Elevation corrections are automatically applied")
    print("4. Night temps are from 6 PM to 6 AM (local time)")
    print("=" * 70)


if __name__ == "__main__":
    main()
