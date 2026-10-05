from functools import lru_cache

import pandas as pd
from django.conf import settings


@lru_cache(maxsize=1)
def load_fuel_stops():
    return pd.read_csv(settings.FUEL_DATA_PATH)
