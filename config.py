"""
Configuration constants for EV Charging Finder application.

Centralizes values used across modules to simplify maintenance and
ensure consistency.  
Adjust these constants to change default behavior, search radius,
and API endpoints without touching business logic.
"""

import os

from dotenv import load_dotenv

load_dotenv()
DEFAULT_LAT = 52.48671
DEFAULT_LON = 13.35544

# Search settings
DEFAULT_CHARGER_RADIUS_KM = 5           # radius for charger lookup
ICE_MODE_CHARGER_RADIUS_KM = 7.5        # 50% larger search radius
CHARGER_RADIUS_KM = DEFAULT_CHARGER_RADIUS_KM
MAX_CHARGERS = 15               # cap number of chargers processed

# ice cream matching thresholds (meters)
DEFAULT_ICE_CREAM_RADIUS_M = 250
MIN_ICE_CREAM_RADIUS_M = 50
MAX_ICE_CREAM_RADIUS_M = 1000
ICE_CREAM_MATCH_RADIUS_M = DEFAULT_ICE_CREAM_RADIUS_M

# Overpass search radius for ice cream POIs (meters)
ICECREAM_SEARCH_RADIUS_M = 3000

OVERPASS_TIMEOUT_SECONDS = 25

# API endpoints
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPEN_CHARGE_MAP_URL = "https://api.openchargemap.io/v3/poi"
OPEN_CHARGE_MAP_KEY = os.getenv('OPEN_CHARGE_MAP_KEY')

# HTTP settings
USER_AGENT = "ev-charging-demo"
REQUEST_TIMEOUT = 15            # seconds

# Cache settings
CACHE_TTL_SECONDS = 600         # 10 minutes
