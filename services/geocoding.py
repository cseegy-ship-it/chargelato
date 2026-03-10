"""
Geocoding service for the EV Charging Finder application.

This module provides functionality to convert a user-entered place
name into geographic coordinates (latitude and longitude).

It uses the OpenStreetMap Nominatim API to perform geocoding.

Functions in this module return coordinates that are used to
center the map and to query nearby EV charging stations and
points of interest.
"""

import requests

from config import DEFAULT_LAT, DEFAULT_LON, NOMINATIM_URL, USER_AGENT, REQUEST_TIMEOUT



def get_coordinates(place: str):
    lat, lon = DEFAULT_LAT, DEFAULT_LON

    if place:
        params = {"q": place, "format": "json", "limit": 1}
        headers = {"User-Agent": USER_AGENT}
        try:
            resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            results = resp.json()
            if results:
                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])
        except requests.RequestException:
            # fall back to defaults on any error
            pass

    return lat, lon