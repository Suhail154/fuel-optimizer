from functools import lru_cache

import requests
from geopy.geocoders import Nominatim

OSRM_URL = 'https://router.project-osrm.org/route/v1/driving'

geocoder = Nominatim(user_agent='fuel-route-optimizer')


@lru_cache(maxsize=256)
def geocode(query):
    try:
        location = geocoder.geocode(query, country_codes='us', timeout=10)
    except Exception:
        return None
    if location is None:
        return None
    return (location.latitude, location.longitude)


class RoutingService:
    def get_route(self, start_location, end_location):
        start = geocode(start_location.strip())
        end = geocode(end_location.strip())
        if not start or not end:
            return {'success': False, 'error': 'Could not geocode one or both locations'}

        url = f'{OSRM_URL}/{start[1]},{start[0]};{end[1]},{end[0]}'
        params = {'overview': 'full', 'geometries': 'geojson'}

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError):
            return {'success': False, 'error': 'Routing service is unavailable'}

        if data.get('code') != 'Ok' or not data.get('routes'):
            return {'success': False, 'error': 'No route found between the two locations'}

        route = data['routes'][0]
        return {
            'success': True,
            'distance_km': route['distance'] / 1000,
            'duration_sec': route['duration'],
            'coordinates': [[lat, lon] for lon, lat in route['geometry']['coordinates']],
            'start_coords': start,
            'end_coords': end,
        }
