from bisect import bisect_right

import numpy as np
from django.conf import settings

EARTH_RADIUS_MILES = 3958.8
MILES_PER_KM = 0.621371
CORRIDOR_MILES = 10
SAMPLE_SPACING_MILES = 2.0
START_PRICE_WINDOW_MILES = 50
MIN_STOP_SPACING_MILES = 150
CHUNK_SIZE = 400


class NoReachableStopError(Exception):
    pass


def haversine_miles(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_MILES * np.arcsin(np.sqrt(a))


class FuelOptimizer:
    def __init__(self, stops):
        self.stops = stops
        self.tank_range = settings.FUEL_TANK_RANGE
        self.mpg = settings.FUEL_EFFICIENCY

    def optimize_route(self, route_result, start_location, end_location):
        route = np.array(route_result['coordinates'], dtype=float)
        total_miles = route_result['distance_km'] * MILES_PER_KM

        if len(route) < 2 or total_miles <= 0:
            return {'success': False, 'error': 'Start and end locations are the same'}

        route_miles = self._route_markers(route, total_miles)
        candidates = self._candidates_along_route(route, route_miles, total_miles)

        try:
            start_price, start_miles, purchases = self._plan(candidates, total_miles)
        except NoReachableStopError as exc:
            return {'success': False, 'error': str(exc)}

        fuel_stops = []
        for index, (stop, miles_bought) in enumerate(purchases):
            next_mile = purchases[index + 1][0]['mile'] if index + 1 < len(purchases) else total_miles
            gallons = miles_bought / self.mpg
            fuel_stops.append({
                'stop_number': index + 1,
                'name': stop['name'],
                'address': stop['address'],
                'city': stop['city'],
                'state': stop['state'],
                'latitude': stop['latitude'],
                'longitude': stop['longitude'],
                'price_per_gallon': round(stop['price'], 3),
                'gallons_to_purchase': round(gallons, 2),
                'estimated_cost': round(gallons * stop['price'], 2),
                'distance_from_start_miles': round(stop['mile'], 1),
                'distance_to_next_stop_miles': round(next_mile - stop['mile'], 1),
                'detour_miles': round(stop['detour'], 1),
            })

        start_gallons = start_miles / self.mpg
        start_cost = start_gallons * start_price
        total_cost = start_cost + sum(
            (miles / self.mpg) * stop['price'] for stop, miles in purchases
        )
        total_gallons = total_miles / self.mpg

        route_data = {
            'start_location': start_location,
            'end_location': end_location,
            'total_distance_miles': round(total_miles, 2),
            'total_distance_km': round(route_result['distance_km'], 2),
            'estimated_duration_hours': round(route_result['duration_sec'] / 3600, 2),
            'starting_fuel_gallons': round(start_gallons, 2),
            'starting_fuel_price_per_gallon': round(start_price, 3),
            'starting_fuel_cost': round(start_cost, 2),
            'fuel_stops': fuel_stops,
            'total_fuel_needed_gallons': round(total_gallons, 2),
            'total_estimated_fuel_cost': round(total_cost, 2),
            'average_price_per_gallon': round(total_cost / total_gallons, 3),
            'route_coordinates': route_result['coordinates'],
            'summary': (
                f"{start_location} to {end_location}: {total_miles:.0f} miles, "
                f"{len(fuel_stops)} fuel stops, ${total_cost:.2f} total fuel cost"
            ),
        }
        return {'success': True, 'route_data': route_data}

    def _route_markers(self, route, total_miles):
        legs = haversine_miles(route[:-1, 0], route[:-1, 1], route[1:, 0], route[1:, 1])
        miles = np.concatenate(([0.0], np.cumsum(legs)))
        if miles[-1] > 0:
            miles *= total_miles / miles[-1]
        return miles

    def _candidates_along_route(self, route, route_miles, total_miles):
        targets = np.arange(0, route_miles[-1] + SAMPLE_SPACING_MILES, SAMPLE_SPACING_MILES)
        keep = np.unique(np.minimum(np.searchsorted(route_miles, targets), len(route) - 1))
        sample, sample_miles = route[keep], route_miles[keep]

        lat_pad = CORRIDOR_MILES / 69.0
        lon_pad = CORRIDOR_MILES / (69.0 * np.cos(np.radians(np.abs(sample[:, 0]).max())))
        stops = self.stops[
            self.stops['latitude'].between(sample[:, 0].min() - lat_pad, sample[:, 0].max() + lat_pad)
            & self.stops['longitude'].between(sample[:, 1].min() - lon_pad, sample[:, 1].max() + lon_pad)
        ]

        lats = stops['latitude'].to_numpy(dtype=float)
        lons = stops['longitude'].to_numpy(dtype=float)
        nearest = np.empty(len(stops), dtype=int)
        distance = np.empty(len(stops), dtype=float)
        for begin in range(0, len(stops), CHUNK_SIZE):
            end = begin + CHUNK_SIZE
            gaps = haversine_miles(
                lats[begin:end, None], lons[begin:end, None],
                sample[None, :, 0], sample[None, :, 1],
            )
            idx = gaps.argmin(axis=1)
            nearest[begin:end] = idx
            distance[begin:end] = gaps[np.arange(len(idx)), idx]

        candidates = []
        rows = stops.reset_index(drop=True)
        for i in np.flatnonzero(distance <= CORRIDOR_MILES):
            mile = float(sample_miles[nearest[i]])
            if mile >= total_miles - 1:
                continue
            row = rows.iloc[i]
            candidates.append({
                'mile': mile,
                'detour': float(distance[i]),
                'price': float(row['Retail Price']),
                'name': row['Truckstop Name'],
                'address': row['Address'],
                'city': row['City'],
                'state': row['State'],
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
            })
        candidates.sort(key=lambda c: c['mile'])
        return candidates

    def _plan(self, candidates, total_miles):
        cap = self.tank_range
        miles = [c['mile'] for c in candidates]

        nearby = [c['price'] for c in candidates if c['mile'] <= START_PRICE_WINDOW_MILES]
        pool = nearby or [c['price'] for c in candidates] or [float(self.stops['Retail Price'].mean())]
        start_price = sum(pool) / len(pool)

        position, fuel, price_here = 0.0, 0.0, start_price
        start_miles, purchases, here = 0.0, [], None

        while True:
            remaining = total_miles - position
            reachable = candidates[bisect_right(miles, position):bisect_right(miles, position + cap)]
            spaced = [c for c in reachable if c['mile'] - position >= MIN_STOP_SPACING_MILES]
            cheaper = next((c for c in spaced if c['price'] < price_here), None)

            if remaining <= cap:
                target = None
                buy = max(0.0, remaining - fuel)
            elif cheaper:
                target = cheaper
                buy = max(0.0, target['mile'] - position - fuel)
            else:
                pool = spaced or reachable
                if not pool:
                    raise NoReachableStopError(
                        f'No fuel stop within {cap} miles after mile {position:.0f} of the route'
                    )
                target = min(pool, key=lambda c: c['price'])
                buy = cap - fuel

            if here is None:
                start_miles = buy
            elif buy > 0:
                purchases.append((here, buy))

            if target is None:
                return start_price, start_miles, purchases

            fuel = max(0.0, fuel + buy - (target['mile'] - position))
            position = target['mile']
            price_here = target['price']
            here = target
