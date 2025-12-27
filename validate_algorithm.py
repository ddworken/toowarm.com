#!/usr/bin/env python3
"""
Validation script for ice climbing assessment algorithm.

Tests the algorithm against real-world observations to check accuracy.
"""

import csv
import sys
from datetime import datetime
from collections import defaultdict
from app import get_historical_ice_climbing_assessment_extended, NCEI_TOKEN

def load_validation_data(filename='validation_data.csv'):
    """Load validation data from CSV file."""
    data = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 3:
                continue

            date_str, location, actual_rating = parts[:3]
            notes = parts[3] if len(parts) > 3 else ''

            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                data.append({
                    'date': date_obj,
                    'location': location,
                    'actual': actual_rating.lower(),
                    'notes': notes
                })
            except ValueError:
                print(f"Warning: Skipping invalid date: {date_str}")
                continue

    return data

def run_validation():
    """Run validation against all test cases."""

    if not NCEI_TOKEN:
        print("⚠️  NCEI_TOKEN not set. Some historical dates may not work.")
        print("Set it with: export NCEI_TOKEN='your_token'")
        print()

    # Load test data
    try:
        test_cases = load_validation_data()
    except FileNotFoundError:
        print("Error: validation_data.csv not found")
        print("Please add your test cases to validation_data.csv")
        return

    if not test_cases:
        print("No validation data found in validation_data.csv")
        print()
        print("Add test cases in this format:")
        print("date,location,actual_rating,notes")
        print("2025-01-10,Leavenworth,poor,Ice was thin")
        print("2025-02-08,White Pine,good,Solid ice formation")
        return

    print("=" * 80)
    print(f"ALGORITHM VALIDATION - Testing {len(test_cases)} Cases")
    print("=" * 80)
    print()

    # Run predictions
    results = []
    for i, test in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] Testing {test['location']} on {test['date']}...", end=' ')
        sys.stdout.flush()

        result = get_historical_ice_climbing_assessment_extended(
            test['location'],
            test['date']
        )

        predicted = result['status']
        actual = test['actual']
        score = result.get('score', 0)
        temps = result.get('temps', [])

        match = predicted == actual
        results.append({
            'date': test['date'],
            'location': test['location'],
            'actual': actual,
            'predicted': predicted,
            'match': match,
            'score': score,
            'temps': temps,
            'notes': test['notes']
        })

        symbol = "✓" if match else "✗"
        print(f"{symbol} (predicted: {predicted}, actual: {actual})")

    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()

    # Calculate metrics
    total = len(results)
    correct = sum(1 for r in results if r['match'])
    accuracy = (correct / total * 100) if total > 0 else 0

    print(f"Overall Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    print()

    # Confusion matrix
    print("Confusion Matrix:")
    print("-" * 60)
    confusion = defaultdict(lambda: defaultdict(int))
    for r in results:
        confusion[r['actual']][r['predicted']] += 1

    # Print matrix
    ratings = ['excellent', 'good', 'poor']
    print(f"{'Actual →':12}", end='')
    for rating in ratings:
        print(f"{rating:12}", end='')
    print()
    print(f"{'Predicted ↓':12}", end='')
    print()

    for pred in ratings:
        print(f"{pred:12}", end='')
        for actual in ratings:
            count = confusion[actual][pred]
            print(f"{count:12}", end='')
        print()

    print()

    # Show incorrect predictions
    incorrect = [r for r in results if not r['match']]
    if incorrect:
        print("=" * 80)
        print(f"INCORRECT PREDICTIONS ({len(incorrect)} cases)")
        print("=" * 80)
        print()

        for r in incorrect:
            print(f"{r['date']} - {r['location']}")
            print(f"  Actual:    {r['actual'].upper()}")
            print(f"  Predicted: {r['predicted'].upper()} (score: {r['score']:.1f}/100)")
            if r['temps']:
                print(f"  Temps:     {min(r['temps'])}-{max(r['temps'])}°F")
            if r['notes']:
                print(f"  Notes:     {r['notes']}")
            print()
    else:
        print("🎉 All predictions were correct!")

    # Show correct predictions for reference
    correct_cases = [r for r in results if r['match']]
    if correct_cases:
        print("=" * 80)
        print(f"CORRECT PREDICTIONS ({len(correct_cases)} cases)")
        print("=" * 80)
        print()

        for r in correct_cases:
            print(f"✓ {r['date']} - {r['location']}: {r['actual'].upper()} (score: {r['score']:.1f}/100)")
            if r['temps']:
                print(f"  Temps: {min(r['temps'])}-{max(r['temps'])}°F")
            if r['notes']:
                print(f"  Notes: {r['notes']}")
            print()

    # Recommendations
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()

    if accuracy >= 80:
        print("✓ Algorithm performing well (≥80% accuracy)")
    elif accuracy >= 60:
        print("⚠️  Algorithm needs tuning (60-80% accuracy)")
        print("   Consider adjusting scoring thresholds")
    else:
        print("✗ Algorithm needs significant adjustment (<60% accuracy)")
        print("   Review temperature scoring function")

    # Analyze score distributions
    if incorrect:
        print()
        print("Score Analysis for Incorrect Predictions:")
        for r in incorrect:
            score = r['score']
            actual = r['actual']
            predicted = r['predicted']

            # Determine how close score was to threshold
            if predicted == 'excellent' and actual != 'excellent':
                print(f"  {r['location']} {r['date']}: Score {score:.1f} (threshold: 75)")
                print(f"    → Suggestion: Consider raising excellent threshold")
            elif predicted == 'good' and actual == 'poor':
                print(f"  {r['location']} {r['date']}: Score {score:.1f} (threshold: 45)")
                print(f"    → Suggestion: Consider raising good threshold")
            elif predicted == 'poor' and actual == 'good':
                print(f"  {r['location']} {r['date']}: Score {score:.1f} (threshold: 45)")
                print(f"    → Suggestion: Consider lowering good threshold")

def main():
    """Main entry point."""
    print()
    print("Ice Climbing Algorithm Validation")
    print("=" * 80)
    print()
    print("This script tests the algorithm against real observations.")
    print("Edit validation_data.csv to add your test cases.")
    print()

    run_validation()

    print()
    print("=" * 80)
    print()
    print("To add more test cases, edit validation_data.csv:")
    print("  Format: date,location,actual_rating,notes")
    print("  Example: 2025-01-10,Leavenworth,good,Solid ice conditions")
    print()

if __name__ == "__main__":
    main()
