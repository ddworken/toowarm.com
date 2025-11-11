"""
Configuration for ice climbing locations to monitor.

Elevation data includes:
- nws_grid_elevation_ft: Elevation of the NWS forecast grid cell
- actual_elevation_ft: Actual climbing site elevation from Mountain Project
- elevation_note: Additional context about the elevation
"""

# Elevation correction configuration
ELEVATION_CONFIG = {
    'enabled': True,
    'lapse_rate_per_1000ft': 3.0,  # Conservative for Pacific Northwest humid maritime climate
    'minimum_correction_threshold': 2.0,  # °F - only flag significant corrections
    'climate_type': 'humid_maritime',  # For documentation
}

LOCATIONS = [
    {
        'name': 'Franklin Falls',
        'latitude': 47.4254,
        'longitude': -121.4320,
        'description': 'Popular waterfall ice climb near Snoqualmie Pass',
        'nws_grid_elevation_ft': 3983,
        'actual_elevation_ft': 2542,
        'elevation_note': 'Waterfall base elevation; NWS grid is 1,441 ft higher'
    },
    {
        'name': 'Exit 38',
        'latitude': 47.4317,
        'longitude': -121.6320,
        'description': 'Ice climbing area off I-90 Exit 38 near North Bend',
        'nws_grid_elevation_ft': 2575,
        'actual_elevation_ft': 1186,
        'elevation_note': 'Main climbing area elevation; NWS grid is 1,389 ft higher'
    },
    {
        'name': 'Alpental',
        'latitude': 47.4432,
        'longitude': -121.4295,
        'description': 'Ski area with ice climbing opportunities near Snoqualmie Pass',
        'nws_grid_elevation_ft': 4862,
        'actual_elevation_ft': 3100,
        'elevation_note': 'Base/parking area elevation; NWS grid is 1,762 ft higher'
    },
    {
        'name': 'Leavenworth',
        'latitude': 47.5962,
        'longitude': -120.6615,
        'description': 'Icicle Creek area ice climbing near Leavenworth',
        'nws_grid_elevation_ft': 1198,
        'actual_elevation_ft': 1965,
        'elevation_note': 'Icicle Creek ice climbing area; climbing sites are 767 ft higher than NWS grid'
    },
    {
        'name': 'White Pine',
        'latitude': 47.78284,
        'longitude': -120.87577,
        'description': 'Ice climbing location in the Cascades',
        'nws_grid_elevation_ft': 2451,
        'actual_elevation_ft': 2319,
        'elevation_note': 'Ice climbing area elevation; minimal difference from NWS grid (132 ft lower)'
    },
    {
        'name': 'Banks Lake',
        'latitude': 47.81441,
        'longitude': -119.1536,
        'description': 'Ice climbing area in Eastern Washington',
        'nws_grid_elevation_ft': 1581,
        'actual_elevation_ft': 2224,
        'elevation_note': 'Climbing area elevation; sites are 643 ft higher than NWS grid'
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
