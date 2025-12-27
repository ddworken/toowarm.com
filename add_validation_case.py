#!/usr/bin/env python3
"""
Helper script to easily add validation cases.

Usage:
    python3 add_validation_case.py

Or provide all arguments:
    python3 add_validation_case.py 2025-01-10 "Leavenworth" good "Solid ice formation"
"""

import sys

def add_case():
    """Add a validation case interactively or from command line."""

    if len(sys.argv) >= 4:
        # Command line mode
        date = sys.argv[1]
        location = sys.argv[2]
        rating = sys.argv[3]
        notes = sys.argv[4] if len(sys.argv) > 4 else ''
    else:
        # Interactive mode
        print("=" * 60)
        print("Add Validation Case")
        print("=" * 60)
        print()

        date = input("Date (YYYY-MM-DD): ").strip()
        location = input("Location: ").strip()

        print()
        print("Rating (enter number):")
        print("  1. excellent - Perfect ice conditions")
        print("  2. good - Solid climbable ice")
        print("  3. poor - Too warm, thin ice, or unsafe")
        print()

        rating_num = input("Rating (1-3): ").strip()
        rating_map = {'1': 'excellent', '2': 'good', '3': 'poor'}
        rating = rating_map.get(rating_num, 'good')

        notes = input("Notes (optional): ").strip()

    # Append to CSV
    with open('validation_data.csv', 'a') as f:
        line = f"{date},{location},{rating}"
        if notes:
            line += f",{notes}"
        f.write(line + '\n')

    print()
    print(f"✓ Added: {date} - {location} - {rating.upper()}")
    if notes:
        print(f"  Notes: {notes}")

    print()
    print(f"Run 'python3 validate_algorithm.py' to test all cases")

if __name__ == "__main__":
    add_case()
