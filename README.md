# Too Warm - Franklin Falls Ice Climbing Weather

A weather monitoring web application for ice climbing conditions at Franklin Falls, Washington. Inspired by [toorainy.com](https://toorainy.com/), but optimized for ice climbing conditions.

## Features

- **Real-time Weather Data**: Fetches current weather forecasts from the National Weather Service API
- **Historical Tracking**: Stores and displays weather data from the past 7 days
- **Color-Coded Conditions**: Easy-to-read table with color coding optimized for ice climbing:
  - **Temperature**: Cold temps (below freezing) highlighted as good conditions
  - **Precipitation**: Snow is good (builds ice), rain is bad (melts ice)
  - **Wind**: Calm conditions preferred for climbing safety
- **Automatic Updates**: Background worker fetches fresh data every hour
- **Single Entry Point**: One command starts both the web server and data collector

## Installation

### Requirements

- Python 3.7+
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Toowarm.con
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Start the Application

Run the main application (starts both web server and background collector):

```bash
python3 app.py
```

The application will:
1. Initialize the SQLite database
2. Start collecting weather data immediately
3. Continue fetching updates every hour
4. Serve the web interface on `http://localhost:5000`

Visit `http://localhost:5000` in your web browser to see the weather conditions.

### Alternative Scripts

Individual components can also be run separately:

#### Original Weather Fetcher (One-time)
```bash
python3 franklin_falls_weather.py
```

#### Weather Collector (Background data collection)
```bash
# Run once and exit
python3 weather_collector.py --once

# Run continuously with custom interval (in seconds)
python3 weather_collector.py --interval=1800  # 30 minutes

# Run continuously with default 1-hour interval
python3 weather_collector.py
```

#### View Historical Data
```bash
# View latest forecast
python3 view_weather_history.py latest

# View fetch history (last 10 by default)
python3 view_weather_history.py history

# View fetch history (custom limit)
python3 view_weather_history.py history 20

# View temperature trends (last 24 hours)
python3 view_weather_history.py trends

# View database statistics
python3 view_weather_history.py stats
```

## Architecture

### Components

1. **app.py**: Main entry point that runs both the Flask web server and weather collector
2. **models.py**: SQLAlchemy database models for storing weather data
3. **franklin_falls_weather.py**: Original simple weather fetcher (displays to console)
4. **weather_collector.py**: Standalone background collector service
5. **view_weather_history.py**: Command-line tool for viewing historical data
6. **templates/index.html**: Web interface template

### Database

The application uses SQLite by default (`franklin_falls_weather.db`) but is designed to easily migrate to PostgreSQL in the future.

#### Database Schema

**weather_forecasts** table:
- `id`: Primary key
- `fetched_at`: Timestamp when data was collected (indexed)
- `period_name`: Forecast period (e.g., "Tonight", "Wednesday")
- `temperature`: Temperature value
- `temperature_unit`: F or C
- `wind_speed`: Wind speed string
- `wind_direction`: Wind direction
- `short_forecast`: Brief forecast description
- `detailed_forecast`: Detailed forecast text
- `grid_id`, `grid_x`, `grid_y`: NWS grid identifiers

### Color Coding

The web interface uses color coding optimized for ice climbing conditions:

**Temperature:**
- Dark Green: ≤20°F (Excellent - cold enough for solid ice)
- Green: 21-32°F (Good - freezing temps)
- Yellow: 33-40°F (Marginal - ice may be soft)
- Red: >40°F (Poor - ice melting)

**Conditions:**
- Dark Green: Snow only (Excellent - builds ice)
- Light Green: Clear/Sunny (Good - stable conditions)
- Yellow: Mixed rain/snow (Marginal)
- Red: Rain (Poor - melts ice)
- Gray: Cloudy/Neutral

**Wind:**
- Dark Green: ≤5 mph (Excellent - calm)
- Light Green: 6-10 mph (Good - light breeze)
- Yellow: 11-15 mph (Marginal)
- Red: >15 mph (Poor - dangerous conditions)

## Data Source

Weather data is sourced from the [National Weather Service API](https://www.weather.gov/documentation/services-web-api):
- Location: Franklin Falls, WA (47.4254, -121.4320)
- Grid: SEW/151,54
- Update frequency: Hourly
- Forecast range: 7 days

## Future Enhancements

- [ ] Migration to PostgreSQL for production
- [ ] Add more ice climbing locations
- [ ] Implement data visualization (charts/graphs)
- [ ] Email/SMS alerts for optimal conditions
- [ ] Historical trend analysis
- [ ] Mobile-responsive improvements
- [ ] Dark mode toggle

## License

This project is open source and available for personal use.

## Acknowledgments

- Inspired by [toorainy.com](https://toorainy.com/)
- Weather data provided by the National Weather Service
- Franklin Falls is a popular ice climbing destination near Snoqualmie Pass, WA