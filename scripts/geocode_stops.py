import re
import sys
from pathlib import Path

import pandas as pd
import zipcodes

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'fuel-prices-for-be-assessment.csv'
TARGET = ROOT / 'fuel-stops-geocoded.csv'


def normalize(name):
    name = re.sub(r'[^A-Z0-9 ]', '', str(name).upper().replace('.', ''))
    name = re.sub(r'\bST\b', 'SAINT', name)
    name = re.sub(r'\bMT\b', 'MOUNT', name)
    name = re.sub(r'\bFT\b', 'FORT', name)
    return re.sub(r'\s+', '', name)


def build_lookup():
    points = {}
    for z in zipcodes.list_all():
        if not z['lat'] or not z['long']:
            continue
        names = [z['city']] + list(z.get('acceptable_cities') or [])
        for name in names:
            key = (normalize(name), z['state'])
            points.setdefault(key, []).append((float(z['lat']), float(z['long'])))
    return {
        key: (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        for key, pts in points.items()
    }


CANADA = {'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'ON', 'PE', 'QC', 'SK', 'YT'}


def main():
    stops = pd.read_csv(SOURCE)
    for column in ('Truckstop Name', 'Address', 'City', 'State'):
        stops[column] = stops[column].astype(str).str.strip()
    stops = stops[~stops['State'].isin(CANADA)]
    stops = stops.sort_values('Retail Price').drop_duplicates('OPIS Truckstop ID')
    stops = stops.sort_values('OPIS Truckstop ID').reset_index(drop=True)
    lookup = build_lookup()
    coords = [
        lookup.get((normalize(row.City), str(row.State).strip().upper()))
        for row in stops.itertuples()
    ]
    stops['latitude'] = [c[0] if c else None for c in coords]
    stops['longitude'] = [c[1] if c else None for c in coords]
    unmatched = stops[stops['latitude'].isna()]
    missing = len(unmatched)
    if missing:
        print(unmatched[['Truckstop Name', 'City', 'State']].to_string(), file=sys.stderr)
    stops = stops.dropna(subset=['latitude', 'longitude'])
    stops.to_csv(TARGET, index=False)
    print(f'{len(stops)} stops written, {missing} unmatched', file=sys.stderr)


if __name__ == '__main__':
    main()
