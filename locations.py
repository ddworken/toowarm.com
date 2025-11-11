"""
Configuration for ice climbing locations to monitor.
"""

LOCATIONS = [
    {
        'name': 'Franklin Falls',
        'latitude': 47.4254,
        'longitude': -121.4320,
        'description': 'Popular waterfall ice climb near Snoqualmie Pass'
    },
    {
        'name': 'Exit 38',
        'latitude': 47.4317,
        'longitude': -121.6320,
        'description': 'Ice climbing area off I-90 Exit 38 near North Bend'
    },
    {
        'name': 'Alpental',
        'latitude': 47.4432,
        'longitude': -121.4295,
        'description': 'Ski area with ice climbing opportunities near Snoqualmie Pass'
    },
    {
        'name': 'Leavenworth',
        'latitude': 47.5962,
        'longitude': -120.6615,
        'description': 'Icicle Creek area ice climbing near Leavenworth'
    },
    {
        'name': 'White Pine',
        'latitude': 47.78284,
        'longitude': -120.87577,
        'description': 'Ice climbing location in the Cascades'
    },
    {
        'name': 'Banks Lake',
        'latitude': 47.81441,
        'longitude': -119.1536,
        'description': 'Ice climbing area in Eastern Washington'
    }
]


def get_location_by_name(name):
    """Get location config by name."""
    for loc in LOCATIONS:
        if loc['name'].lower() == name.lower():
            return loc
    return None


def get_all_locations():
    """Get all configured locations."""
    return LOCATIONS
