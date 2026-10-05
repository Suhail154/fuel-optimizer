# Fuel Route Optimizer

Django REST API that takes a start and end location in the USA, returns the driving route, and plans fuel stops along it using the supplied truck stop prices.

Vehicle: 500 mile range, 10 MPG.

## Setup

Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

With the server running, `python test_api.py` in a second terminal runs the API checks.

## Endpoints

`POST /api/optimize-route/`

```json
{"start_location": "New York, NY", "end_location": "Los Angeles, CA"}
```

Returns distance, duration, `route_coordinates` as `[lat, lon]` pairs, the planned `fuel_stops` (name, location, price per gallon, gallons bought, cost, miles from start), and the total fuel cost.

`GET /api/fuel-stops/?state=TX&limit=10` lists the cheapest stops in a state.

`GET /api/health/`

## How it works

- Start and end are geocoded with Nominatim.
- One request to the public OSRM server returns the full route geometry, distance and duration.
- Stops within 10 miles of the route are candidates, positioned by miles along the route.
- A greedy planner buys just enough fuel to reach the next cheaper stop at least 150 miles ahead, and fills the tank when none is cheaper. If the destination is within range, no stop is planned.
- Fuel for the first leg is assumed bought at the origin, at the average price of stops within 50 miles of it.
- Total cost is gallons used (distance / 10) priced at the stop where each gallon was bought.

## Data

The supplied CSV has no coordinates, so `scripts/geocode_stops.py` builds `fuel-stops-geocoded.csv` (committed) by matching each stop's city and state against the `zipcodes` package (`pip install zipcodes` to regenerate). Coordinates are city-level, so a stop can be several miles from its real position. Canadian rows are dropped, and stops that appear multiple times are reduced to their lowest listed price.
