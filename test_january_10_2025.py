#!/usr/bin/env python3
"""
Test the historical ice climbing assessment for January 10, 2025.

This demonstrates using the NCEI CDO API for dates beyond the 7-day NWS limit.
"""

from app import get_historical_ice_climbing_assessment_extended, NCEI_TOKEN
from datetime import date

def main():
    print("=" * 80)
    print("HISTORICAL ICE CLIMBING ASSESSMENT - JANUARY 10, 2025")
    print("=" * 80)
    print()

    # The target date
    target_date = date(2025, 1, 10)

    print(f"Target Date: {target_date.strftime('%B %d, %Y')}")
    print(f"Days ago: {(date.today() - target_date).days} days")
    print()

    # Check if token is set
    if not NCEI_TOKEN:
        print("⚠️  NCEI_TOKEN not set")
        print()
        print("This date is beyond the 7-day limit of the NWS API.")
        print("To access historical data from January 2025, you need an NCEI token.")
        print()
        print("Quick Setup:")
        print("  1. Visit: https://www.ncdc.noaa.gov/cdo-web/token")
        print("  2. Enter your email and get instant token")
        print("  3. Run: export NCEI_TOKEN='your_token_here'")
        print("  4. Run this script again")
        print()
        print("Attempting anyway (will show error message)...")
        print()

    # Test with multiple locations
    locations = ['Franklin Falls', 'Leavenworth', 'Alpental']

    for location in locations:
        print("-" * 80)
        print(f"Location: {location}")
        print("-" * 80)

        result = get_historical_ice_climbing_assessment_extended(location, target_date)

        print(f"  Assessment: {result['status'].upper()}")
        print(f"  Data Source: {result['data_source']}")
        print(f"  Station: {result['station_id']}")

        if result.get('station_name'):
            print(f"  Station Name: {result['station_name']}")

        if result['date_range'][0] and result['date_range'][1]:
            print(f"  Data Range: {result['date_range'][0]} to {result['date_range'][1]}")

        if result['temps']:
            print(f"  Night Temps (past 5 days): {result['temps']}")
            print(f"  Min: {min(result['temps'])}°F, Max: {max(result['temps'])}°F")

        print(f"  Message: {result['message']}")
        print()

        # Interpretation
        if result['status'] == 'excellent':
            print("  🎉 EXCELLENT! All lows ≤20°F - perfect ice formation")
        elif result['status'] == 'good':
            print("  ✓ GOOD! All lows ≤25°F - solid ice conditions")
        elif result['status'] == 'poor':
            print("  ⚠️  POOR - Temps too warm for good ice")
        else:
            print(f"  ℹ️  {result['message']}")

        print()

    print("=" * 80)
    if NCEI_TOKEN:
        print("✓ Successfully retrieved historical data using NCEI CDO API")
    else:
        print("Set NCEI_TOKEN to retrieve actual historical data from January 2025")
    print("=" * 80)

if __name__ == "__main__":
    main()
