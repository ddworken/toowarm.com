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
        'elevation_note': 'Waterfall base elevation; NWS grid is 1,441 ft higher',
        'nwac_zone_id': '3',
        'nwac_zone_name': 'Snoqualmie Pass',
        'links': [
            {'name': 'Mountain Project', 'url': 'https://www.mountainproject.com/area/117973219/franklin-falls'},
            {'name': 'AllTrails', 'url': 'https://www.alltrails.com/trail/us/washington/franklin-falls-trail'}
        ]
    },
    {
        'name': 'Exit 38',
        'latitude': 47.4317,
        'longitude': -121.6320,
        'description': 'Ice climbing area off I-90 Exit 38 near North Bend',
        'nws_grid_elevation_ft': 2575,
        'actual_elevation_ft': 1186,
        'elevation_note': 'Main climbing area elevation; NWS grid is 1,389 ft higher',
        'nwac_zone_id': '3',
        'nwac_zone_name': 'Snoqualmie Pass',
        'links': [
            {'name': 'Mountain Project', 'url': 'https://www.mountainproject.com/area/120086752/dry-tooling-ice-climbing-at-exit-38'}
        ]
    },
    {
        'name': 'Alpental',
        'latitude': 47.4432,
        'longitude': -121.4295,
        'description': 'Ski area with ice climbing opportunities near Snoqualmie Pass',
        'nws_grid_elevation_ft': 4862,
        'actual_elevation_ft': 3100,
        'elevation_note': 'Base/parking area elevation; NWS grid is 1,762 ft higher',
        'nwac_zone_id': '3',
        'nwac_zone_name': 'Snoqualmie Pass',
        'links': [
            {'name': 'Mountain Project', 'url': 'https://www.mountainproject.com/route-finder?selectedIds=108471741&type=ice&diffMinrock=1400&diffMinboulder=20000&diffMinaid=70000&diffMinice=30000&diffMinmixed=50000&diffMaxrock=4800&diffMaxboulder=20050&diffMaxaid=75260&diffMaxice=38500&diffMaxmixed=65050&is_trad_climb=1&is_sport_climb=1&is_top_rope=1&stars=0&pitches=0&sort1=area&sort2=rating'}
        ]
    },
    {
        'name': 'Leavenworth',
        'latitude': 47.5962,
        'longitude': -120.6615,
        'description': 'Icicle Creek area ice climbing near Leavenworth',
        'nws_grid_elevation_ft': 1198,
        'actual_elevation_ft': 1965,
        'elevation_note': 'Icicle Creek ice climbing area; climbing sites are 767 ft higher than NWS grid',
        'nwac_zone_id': '8',
        'nwac_zone_name': 'East Slopes Central',
        'links': [
            {'name': 'Mountain Project', 'url': 'https://www.mountainproject.com/area/120322449/ice-climbing-in-icicle-creek'}
        ]
    },
    {
        'name': 'White Pine',
        'latitude': 47.78284,
        'longitude': -120.87577,
        'description': 'Ice climbing location in the Cascades',
        'nws_grid_elevation_ft': 2451,
        'actual_elevation_ft': 2319,
        'elevation_note': 'Ice climbing area elevation; minimal difference from NWS grid (132 ft lower)',
        'nwac_zone_id': '2',
        'nwac_zone_name': 'Stevens Pass',
        'links': [
            {'name': 'Mountain Project', 'url': 'https://www.mountainproject.com/area/120310945/whitepine-ice-mixed'}
        ]
    },
    {
        'name': 'Banks Lake',
        'latitude': 47.81441,
        'longitude': -119.1536,
        'description': 'Ice climbing area in Eastern Washington',
        'nws_grid_elevation_ft': 1581,
        'actual_elevation_ft': 2224,
        'elevation_note': 'Climbing area elevation; sites are 643 ft higher than NWS grid',
        'nwac_zone_id': None,
        'nwac_zone_name': None,
        'links': [
            {'name': 'Mountain Project', 'url': 'https://www.mountainproject.com/area/116630932/banks-lake-ice-climbing'}
        ]
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
