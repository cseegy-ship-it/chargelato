"""
Geocoding service for the EV Charging Finder application.

Converts user-entered place names to geographic coordinates (lat/lon) and
extracts country code using the OpenStreetMap Nominatim API.

Results are cached for 10 minutes to minimize API calls and respect rate limits.

Functions:
- get_coordinates(place) → (lat, lon, country_code) tuple
"""

from typing import Tuple

import requests
import streamlit as st

from config import DEFAULT_LAT, DEFAULT_LON, NOMINATIM_URL, USER_AGENT, REQUEST_TIMEOUT


@st.cache_data(ttl=600, show_spinner=False)
def get_coordinates(place: str) -> Tuple[float, float, str]:
    """Convert a place name to geographic coordinates and country code.

    Uses OpenStreetMap Nominatim API to geocode the input and extract the
    country code. Falls back to defaults if the place is empty or the request fails.

    Results are cached for 10 minutes to minimize API calls and respect Nominatim's
    rate limits (1 request per second).

    Args:
        place: Location name to geocode (e.g., "Berlin" or "Leberstraße 2")

    Returns:
        (lat, lon, country_code) tuple. Country code defaults to "DE" if not found.
    """
    lat, lon = DEFAULT_LAT, DEFAULT_LON
    country_code = "DE"  # Default country code

    if place:
        params = {"q": place, "format": "json", "limit": 1}
        headers = {"User-Agent": USER_AGENT}

        try:
            resp = requests.get(
                NOMINATIM_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT
            )

            # Handle rate limiting gracefully
            if resp.status_code == 429:
                print("⚠️  Rate limit reached, using cached result")
                return lat, lon, country_code

            resp.raise_for_status()
            results = resp.json()

            if results:
                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])

                # Extract country code from address dict
                address = results[0].get("address", {})
                cc = address.get("country_code", "").upper()
                if cc:
                    country_code = cc

                print(f"📍 Geocoded '{place}' to ({lat}, {lon}) in {country_code}")

        except requests.RequestException as e:
            print(f"⚠️  Geocoding failed for '{place}': {e}")

    return lat, lon, country_code
