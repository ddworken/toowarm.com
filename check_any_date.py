#!/usr/bin/env python3
"""
Easy script to check ice climbing conditions for any historical date.

Usage:
    python3 check_any_date.py 2025-01-10
    python3 check_any_date.py 2025-02-08
    python3 check_any_date.py 2024-12-25
"""

import sys
from datetime import datetime
from app import get_historical_ice_climbing_assessment_extended, NCEI_TOKEN

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_any_date.py YYYY-MM-DD")
        print("Example: python3 check_any_date.py 2025-01-10")
        sys.exit(1)

    # Parse date
    try:
        date_str = sys.argv[1]
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        print(f"Error: Invalid date format '{date_str}'. Use YYYY-MM-DD")
        sys.exit(1)

    # Check token
    if not NCEI_TOKEN:
        print("⚠️  NCEI_TOKEN not set. Historical data may not be available.")
        print("Get free token: https://www.ncdc.noaa.gov/cdo-web/token")
        print("Then run: export NCEI_TOKEN='your_token'")
        print()

    print("=" * 80)
    print(f"ICE CLIMBING ASSESSMENT FOR {target_date.strftime('%B %d, %Y').upper()}")
    print("=" * 80)
    print()

    locations = [
        'Franklin Falls',
        'Leavenworth',
        'Alpental',
        'White Pine',
        'Exit 38',
        'Banks Lake'
    ]

    for location in locations:
        result = get_historical_ice_climbing_assessment_extended(location, target_date)

        # Status symbol
        symbols = {
            'excellent': '🎉 ✓✓✓',
            'good': '✓✓',
            'poor': '⚠️  ✗',
            'unknown': '? '
        }
        symbol = symbols.get(result['status'], '? ')

        print(f"{symbol} {location:20} {result['status'].upper():10}", end='')

        if result['temps']:
            min_temp = min(result['temps'])
            max_temp = max(result['temps'])
            print(f" {min_temp}-{max_temp}°F", end='')

        print()

    print()
    print("=" * 80)
    print("Legend (Smooth Scoring System):")
    print("  ✓✓✓ EXCELLENT - Score ≥78/100 (consistently very cold, great ice)")
    print("  ✓✓  GOOD - Score ≥45/100 (cold enough for solid ice)")
    print("  ✗   POOR - Score <45/100 (too warm, unreliable ice)")
    print()
    print("  Score based on 5-day average: 0°F=100pts, 40°F=0pts")
    print("  No harsh penalties - 26°F only slightly worse than 25°F")
    print("=" * 80)

if __name__ == "__main__":
    main()
