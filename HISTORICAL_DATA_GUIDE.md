# Historical Weather Data Guide

This guide explains how to retrieve historical weather data for ice climbing assessments.

## Overview

The ice climbing assessment system can calculate historical assessments using observed weather data. However, there are two different APIs depending on how far back you need data:

### 1. NWS API (Last 6-7 Days) ✅ **Implemented**

**Coverage:** Last 6-7 days only
**Function:** `get_historical_ice_climbing_assessment(location_name, target_date)`
**No API key required**

#### Usage Example:

```python
from app import get_historical_ice_climbing_assessment
from datetime import datetime, timedelta

# Get assessment for 3 days ago
target_date = datetime.now().date() - timedelta(days=3)
result = get_historical_ice_climbing_assessment('Franklin Falls', target_date)

print(f"Status: {result['status']}")
print(f"Message: {result['message']}")
print(f"Night temps: {result['temps']}")
```

#### How It Works:

1. **Find Weather Station**: Automatically finds the nearest NWS observation station
2. **Fetch Observations**: Retrieves ~1000 observations (every 10 minutes) for the past week
3. **Extract Night Temps**: Filters temperatures from 6 PM to 6 AM
4. **Apply Corrections**: Automatically applies elevation corrections
5. **Calculate Assessment**: Uses the standard 5-day rolling assessment logic

#### Limitations:

- Only ~6-7 days of data available
- For older dates, you'll get an error message directing you to use NCEI CDO API

---

### 2. NCEI Climate Data Online (CDO) API (All Historical Data) 🔨 **Not Yet Implemented**

**Coverage:** Historical data going back 100+ years
**API Endpoint:** `https://www.ncei.noaa.gov/cdo-web/api/v2/`
**Requires:** Free API token (request at https://www.ncdc.noaa.gov/cdo-web/token)

#### To Implement This:

**Step 1: Get API Token**
- Visit: https://www.ncdc.noaa.gov/cdo-web/token
- Enter your email address
- Receive token via email (usually instant)
- Rate limits: 5 requests/second, 10,000 requests/day

**Step 2: Find Nearby Stations**

```python
import requests

CDO_TOKEN = "your_token_here"
headers = {"token": CDO_TOKEN}

# Find stations near a location
lat, lon = 47.4254, -121.4320  # Franklin Falls
params = {
    "datasetid": "GHCND",  # Global Historical Climatology Network Daily
    "datatypeid": "TMIN",   # Minimum temperature
    "extent": f"{lat-0.1},{lon-0.1},{lat+0.1},{lon+0.1}",  # Bounding box
    "limit": 10
}

response = requests.get(
    "https://www.ncei.noaa.gov/cdo-web/api/v2/stations",
    headers=headers,
    params=params
)
stations = response.json()
```

**Step 3: Get Historical Data**

```python
from datetime import datetime, timedelta

station_id = "GHCND:USC00454174"  # Example station
start_date = "2024-01-01"
end_date = "2024-01-31"

params = {
    "datasetid": "GHCND",
    "stationid": station_id,
    "datatypeid": "TMIN",  # Minimum temperature
    "startdate": start_date,
    "enddate": end_date,
    "units": "standard",  # Returns Fahrenheit
    "limit": 1000
}

response = requests.get(
    "https://www.ncei.noaa.gov/cdo-web/api/v2/data",
    headers=headers,
    params=params
)

data = response.json()
for record in data['results']:
    date = record['date'][:10]
    tmin = record['value']  # Already in Fahrenheit
    print(f"{date}: {tmin}°F")
```

**Step 4: Integrate with Assessment Function**

To create a full historical assessment function:

```python
def get_extended_historical_assessment(location_name, target_date, ncei_token):
    """
    Get historical assessment for any date using NCEI CDO API.

    Args:
        location_name: Ice climbing location
        target_date: Date to assess (can be years in the past)
        ncei_token: NCEI API token

    Returns:
        dict: Same format as get_historical_ice_climbing_assessment
    """
    # 1. Find nearest GHCND station for the location
    # 2. Request TMIN data for target_date - 5 days to target_date
    # 3. Apply elevation corrections to TMIN values
    # 4. Calculate rolling assessment using existing function
    # 5. Return result
    pass
```

---

## Comparison: NWS API vs NCEI CDO API

| Feature | NWS API | NCEI CDO API |
|---------|---------|--------------|
| **Coverage** | Last 6-7 days | 100+ years |
| **API Key** | Not required | Free token required |
| **Rate Limit** | None specified | 5/sec, 10k/day |
| **Data Frequency** | Every 10 min | Daily minimums |
| **Implementation** | ✅ Complete | ⚠️ Needs token + code |
| **Accuracy** | High (raw obs) | High (quality controlled) |
| **Elevation Correction** | ✅ Applied | ⚠️ Need to implement |

---

## Data Quality Notes

### Night Temperature Definition

Both systems use different approaches:

- **NWS API (current)**: Extracts actual observations from 6 PM to 6 AM, finds minimum
- **NCEI CDO (TMIN)**: Provides daily minimum temperature (00:00-23:59)

The TMIN may not always be the "night" minimum, but it's typically very close and is the standard for climatological analysis.

### Elevation Corrections

The current implementation automatically applies elevation corrections to match climbing site elevations. When implementing NCEI CDO:

1. Retrieve the station's elevation from station metadata
2. Apply the same `apply_elevation_correction()` function
3. Use the corrected temperatures for assessment

### Station Selection

- **NWS API**: Uses nearest observing station (usually at an airport or mountain pass)
- **NCEI CDO**: Use stations with good TMIN data coverage; check station metadata for:
  - Date range coverage (mindate/maxdate)
  - Data coverage percentage
  - Elevation (for better matching)

---

## Example Implementation Roadmap

If you want to add full historical support:

1. **Get NCEI Token** (5 minutes)
   - Visit https://www.ncdc.noaa.gov/cdo-web/token
   - Add to environment variable: `NCEI_TOKEN=your_token`

2. **Create Station Mapping** (1 hour)
   - Find GHCND stations near each climbing location
   - Store in `locations.py` as `ncei_station_id`
   - Verify data coverage and elevation match

3. **Implement Data Fetcher** (2 hours)
   - Write `get_ncei_tmin_data()` function
   - Handle pagination (API returns max 1000 records)
   - Parse response and convert to temperature list

4. **Integrate with Assessment** (1 hour)
   - Modify or create new function to use NCEI data
   - Apply elevation corrections
   - Use existing `calculate_rolling_assessment()`

5. **Add Caching** (1 hour)
   - Cache NCEI responses to respect rate limits
   - Store in database or file cache
   - Historical data doesn't change, so permanent cache is fine

**Total effort:** ~5 hours

---

## Resources

- **NWS API Documentation**: https://www.weather.gov/documentation/services-web-api
- **NCEI CDO API Docs**: https://www.ncdc.noaa.gov/cdo-web/webservices/v2
- **NCEI Token Request**: https://www.ncdc.noaa.gov/cdo-web/token
- **Dataset Info**: https://www.ncdc.noaa.gov/cdo-web/datasets
- **GHCND Documentation**: https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily

---

## Current Implementation Status

✅ **Completed:**
- NWS API integration for last 7 days
- Weather station discovery
- Observation fetching and parsing
- Night temperature extraction (6 PM - 6 AM)
- Elevation correction application
- Assessment calculation
- Error handling and messaging

⏳ **To Do (for full historical support):**
- NCEI CDO API integration
- Station mapping for all locations
- TMIN data fetching
- Response caching
- Date range validation
