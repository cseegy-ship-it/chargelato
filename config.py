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
CHARGER_RADIUS_KM = 5           # radius for charger lookup
MAX_CHARGERS = 15               # cap number of chargers processed

# API endpoints
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPEN_CHARGE_MAP_URL = "https://api.openchargemap.io/v3/poi"
OPEN_CHARGE_MAP_KEY = os.getenv('OPEN_CHARGE_MAP_KEY')

# HTTP settings
USER_AGENT = "ev-charging-demo"
REQUEST_TIMEOUT = 15            # seconds

# Cache settings
CACHE_TTL_SECONDS = 600         # 10 minutes
