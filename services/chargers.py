"""
EV Charging Stations service for the EV Charging Finder application.

This module provides functionality to retrieve nearby EV charging stations
from the Open Charge Map API and parse the response data.

The Open Charge Map API is queried based on a user's geographic coordinates and a 
specified search radius to find relevant charging stations for display on the map.

Functions in this module handle API communication and data extraction,
ensuring robust handling of missing or incomplete data.
"""

import requests
import time

from config import (
    CHARGER_RADIUS_KM,
    MAX_CHARGERS,
    OPEN_CHARGE_MAP_URL,
    OPEN_CHARGE_MAP_KEY,
    REQUEST_TIMEOUT,
    USER_AGENT,
    CACHE_TTL_SECONDS,
)

# internal cache to reduce redundant Open Charge Map requests
_cache = {}  # key -> (result, timestamp)


def get_chargers(lat, lon, radius_km=CHARGER_RADIUS_KM):
    """
    Return a limited list of nearby chargers using Open Charge Map API.

    Caches results briefly to avoid hitting API rate limits. The
    returned list is truncated to MAX_CHARGERS to keep rendering fast.
    """
    key = (round(lat, 5), round(lon, 5), radius_km)
    now = time.time()
    if key in _cache:
        result, ts = _cache[key]
        if now - ts < CACHE_TTL_SECONDS:
            return result

    print(f"🔎 Fetching chargers near: {lat}, {lon}")
    chargers = []

    params = {
        "key": OPEN_CHARGE_MAP_KEY,
        "latitude": lat,
        "longitude": lon,
        "distance": radius_km,
        "distanceunit": "KM",
        "maxresults": MAX_CHARGERS,
        "compact": False,
        "verbose": False,
    }

    try:
        resp = requests.get(OPEN_CHARGE_MAP_URL, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            print("⚠️  Open Charge Map API request failed")
            return []

        data = resp.json()
        if not isinstance(data, list):
            return []

        for poi in data:
            addr = poi.get("AddressInfo", {})
            name = addr.get("Title", "Unnamed Charging Station")
            lat_e = addr.get("Latitude")
            lon_e = addr.get("Longitude")

            if not lat_e or not lon_e:
                continue

            # Extract power and plug info from first connection
            power = None
            plug = "Unknown"
            connections = poi.get("Connections", [])
            
            if connections:
                connection = connections[0]
                power = connection.get("PowerKW")
                conn_type = connection.get("ConnectionType", {})
                plug = conn_type.get("Title", "Unknown") if isinstance(conn_type, dict) else "Unknown"

            print(f"🔎 Station: {name}")
            print(f"🔌 Connector: {plug}")
            print(f"⚡ Power: {power}")

            charger_entry = {
                "name": name,
                "lat": lat_e,
                "lon": lon_e,
                "power": power,
                "plug": plug,
            }
            chargers.append(charger_entry)

    except requests.RequestException:
        print("⚠️  Open Charge Map API request failed")
        return []

    print(f"⚡ Chargers returned: {len(chargers)}")
    _cache[key] = (chargers, now)
    return chargers
