"""
EV Charging Stations service for the EV Charging Finder application.

Fetches nearby EV charging stations from the Open Charge Map API.
Implements caching to reduce redundant requests.

Functions:
- get_chargers(lat, lon, radius_km) → list of normalized charger dicts
"""

import time
from typing import Optional

import requests

from config import (
    CHARGER_RADIUS_KM,
    MAX_CHARGERS,
    OPEN_CHARGE_MAP_URL,
    OPEN_CHARGE_MAP_KEY,
    REQUEST_TIMEOUT,
    USER_AGENT,
    CACHE_TTL_SECONDS,
)

# Internal cache: (lat, lon, radius) → (chargers_list, timestamp)
_CACHE: dict = {}


def _extract_connection_info(connections: list) -> tuple[Optional[float], str]:
    """Extract power and plug type from first connection in list.

    Args:
        connections: List of connection dicts from OCM API

    Returns:
        (power_kw, plug_type): Power in kW and plug type string
    """
    if not connections:
        return None, "Unknown"

    conn = connections[0]
    power = conn.get("PowerKW")
    conn_type = conn.get("ConnectionType", {})
    plug = (
        conn_type.get("Title", "Unknown")
        if isinstance(conn_type, dict)
        else "Unknown"
    )

    return power, plug


def get_chargers(lat: float, lon: float, radius_km: float = CHARGER_RADIUS_KM) -> list:
    """Fetch nearby EV charging stations from Open Charge Map API.

    Results are cached briefly to avoid hitting rate limits. Returns a list
    capped at MAX_CHARGERS for performance.

    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        radius_km: Search radius in kilometers

    Returns:
        List of charger dicts with keys: name, lat, lon, power, plug
    """
    # Check cache
    cache_key = (round(lat, 5), round(lon, 5), radius_km)
    now = time.time()

    if cache_key in _CACHE:
        chargers, timestamp = _CACHE[cache_key]
        if now - timestamp < CACHE_TTL_SECONDS:
            return chargers

    print(f"⚡ Fetching chargers near: {lat}, {lon}")
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
        resp = requests.get(
            OPEN_CHARGE_MAP_URL, params=params, timeout=REQUEST_TIMEOUT
        )
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

            power, plug = _extract_connection_info(poi.get("Connections", []))

            print(f"🔎 Station: {name}")
            print(f"🔌 Connector: {plug} | ⚡ Power: {power}")

            charger_entry = {
                "name": name,
                "lat": lat_e,
                "lon": lon_e,
                "power": power,
                "plug": plug,
            }
            chargers.append(charger_entry)

    except requests.RequestException as e:
        print(f"⚠️  Open Charge Map request failed: {e}")
        return []

    print(f"⚡ Chargers returned: {len(chargers)}")
    _CACHE[cache_key] = (chargers, now)
    return chargers
