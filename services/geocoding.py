"""
Geocoding service for the EV Charging Finder application.

Converts user-entered place names to geographic coordinates (lat/lon)
using the OpenStreetMap Nominatim API.

Functions:
- get_coordinates(place) → (lat, lon) tuple
"""

from typing import Tuple

import requests

from config import DEFAULT_LAT, DEFAULT_LON, NOMINATIM_URL, USER_AGENT, REQUEST_TIMEOUT


def get_coordinates(place: str) -> Tuple[float, float]:
    """Convert a place name to geographic coordinates.

    Uses OpenStreetMap Nominatim API to geocode the input. Falls back to
    default coordinates if the place is empty or the request fails.

    Args:
        place: Location name to geocode (e.g., "Berlin" or "Leberstraße 2")

    Returns:
        (lat, lon) tuple, or defaults (52.48671, 13.35544) if not found
    """
    lat, lon = DEFAULT_LAT, DEFAULT_LON

    if place:
        params = {"q": place, "format": "json", "limit": 1}
        headers = {"User-Agent": USER_AGENT}

        try:
            resp = requests.get(
                NOMINATIM_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            results = resp.json()

            if results:
                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])
                print(f"📍 Geocoded '{place}' to ({lat}, {lon})")

        except requests.RequestException as e:
            print(f"⚠️  Geocoding failed for '{place}': {e}")

    return lat, lon
