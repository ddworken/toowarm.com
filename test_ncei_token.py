#!/usr/bin/env python3
"""
Test script to verify NCEI token is working.
"""

import os
import sys
from app import NCEI_TOKEN, find_ncei_stations

def test_token():
    print("=" * 70)
    print("NCEI TOKEN TEST")
    print("=" * 70)
    print()

    if not NCEI_TOKEN:
        print("❌ NCEI_TOKEN environment variable is NOT set")
        print()
        print("To get a token:")
        print("  1. Visit: https://www.ncdc.noaa.gov/cdo-web/token")
        print("  2. Enter your email")
        print("  3. Check your email for the token")
        print("  4. Run: export NCEI_TOKEN='your_token_here'")
        print()
        sys.exit(1)

    print(f"✓ NCEI_TOKEN is set: {NCEI_TOKEN[:10]}...")
    print()

    # Test by searching for stations near Franklin Falls
    print("Testing API with Franklin Falls location...")
    stations = find_ncei_stations(47.4254, -121.4320, radius_miles=30)

    if stations:
        print(f"✓ Found {len(stations)} stations")
        print()
        print("First 3 stations:")
        for i, station in enumerate(stations[:3], 1):
            print(f"  {i}. {station['name']}")
            print(f"     ID: {station['id']}")
            print(f"     Elevation: {station['elevation']} m")
            print(f"     Data: {station['mindate']} to {station['maxdate']}")
            print(f"     Coverage: {station['datacoverage']*100:.1f}%")
            print()

        print("=" * 70)
        print("✓ NCEI Token is working correctly!")
        print("=" * 70)
    else:
        print("❌ No stations found. Check your token or try a different location.")
        sys.exit(1)

if __name__ == "__main__":
    test_token()
