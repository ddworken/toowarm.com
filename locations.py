"""
Configuration for ice climbing locations to monitor.

Locations are loaded from locations.yaml in the repo root.
"""

import os
import yaml

# Elevation correction configuration
ELEVATION_CONFIG = {
    'enabled': True,
    'lapse_rate_per_1000ft': 3.0,  # Conservative for Pacific Northwest humid maritime climate
    'minimum_correction_threshold': 2.0,  # °F - only flag significant corrections
    'climate_type': 'humid_maritime',  # For documentation
}

def _load_locations():
    """Load locations from YAML file."""
    yaml_path = os.path.join(os.path.dirname(__file__), 'locations.yaml')
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    locations = []
    for loc in data['locations']:
        # Transform YAML format to internal format
        elevation_diff = loc['nws_grid_elevation_ft'] - loc['elevation_ft']
        if elevation_diff > 0:
            elevation_note = f"NWS grid is {elevation_diff:,} ft higher than climbing area"
        elif elevation_diff < 0:
            elevation_note = f"Climbing area is {-elevation_diff:,} ft higher than NWS grid"
        else:
            elevation_note = "NWS grid matches climbing area elevation"

        locations.append({
            'name': loc['name'],
            'description': loc.get('description', f"Ice climbing near {loc['nwac_zone_name'] or loc['name']}"),
            'latitude': loc['latitude'],
            'longitude': loc['longitude'],
            'actual_elevation_ft': loc['elevation_ft'],
            'nws_grid_elevation_ft': loc['nws_grid_elevation_ft'],
            'elevation_note': elevation_note,
            'nwac_zone_id': loc['nwac_zone_id'],
            'nwac_zone_name': loc['nwac_zone_name'],
            'links': [{'name': 'Mountain Project', 'url': loc['mountain_project_url']}] if loc.get('mountain_project_url') else []
        })

    return locations

LOCATIONS = _load_locations()


def get_location_by_name(name):
    """Get location config by name."""
    for loc in LOCATIONS:
        if loc['name'].lower() == name.lower():
            return loc
    return None


def get_all_locations():
    """Get all configured locations."""
    return LOCATIONS
