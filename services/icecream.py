"""
Ice cream points-of-interest service for the EV Charging Finder application.

Queries Overpass API for ice cream shops (amenity=ice_cream or shop=ice_cream)
near given coordinates. Implements caching and server fallback for resilience.

Functions:
- get_icecream_pois(lat, lon, radius_m) → list of POI dicts
- filter_chargers_by_icecream(chargers, pois, max_dist_m) → (filtered, matches)
"""

import math
import time
from typing import List, Tuple

import requests
import streamlit as st

from config import (
    OVERPASS_TIMEOUT_SECONDS,
    REQUEST_TIMEOUT,
    ICE_CREAM_MATCH_RADIUS_M,
    ICECREAM_SEARCH_RADIUS_M,
)

PRIMARY_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
FALLBACK_OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two lat/lon coordinates.

    Uses the haversine formula for great-circle distance.

    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate

    Returns:
        Distance in meters
    """
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _query_overpass(query: str, server_url: str) -> dict:
    """Query Overpass server with retry logic on 504 errors.

    Args:
        query: Overpass QL query string
        server_url: Server URL to query

    Returns:
        Response JSON dict, or empty dict on failure
    """
    print(f"🌍 Overpass server: {server_url}")

    try:
        resp = requests.post(server_url, data=query, timeout=30)
    except requests.RequestException as e:
        print(f"⚠️  Overpass request exception: {e}")
        return {}

    print(f"🍦 Overpass status: {resp.status_code}")

    # Retry once on gateway timeout
    if resp.status_code == 504:
        print("🍦 504 received, retrying after delay...")
        time.sleep(2)
        try:
            resp = requests.post(server_url, data=query, timeout=30)
            print(f"🍦 Overpass status (retry): {resp.status_code}")
        except requests.RequestException as e:
            print(f"⚠️  Overpass retry exception: {e}")
            return {}

    if resp.status_code != 200:
        print("⚠️  Overpass API request failed")
        print(f"⚠️  Response preview: {resp.text[:300]}")
        return {}

    try:
        return resp.json()
    except ValueError:
        print("⚠️  Overpass JSON parsing failed")
        return {}


@st.cache_data(ttl=600, show_spinner=False)
def get_icecream_pois(lat: float, lon: float, radius_m: float) -> List[dict]:
    """Fetch nearby ice cream shops from Overpass API.

    Implements retry logic and server fallback for resilience. Results are
    cached for 10 minutes to avoid redundant queries.

    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        radius_m: Search radius in meters

    Returns:
        List of POI dicts with keys: name, lat, lon
    """
    print("🍦 Fetching ice cream POIs...")

    query = f"""[out:json][timeout:{OVERPASS_TIMEOUT_SECONDS}];
(
  node(around:{ICECREAM_SEARCH_RADIUS_M},{lat},{lon})[\"amenity\"=\"ice_cream\"];
  way(around:{ICECREAM_SEARCH_RADIUS_M},{lat},{lon})[\"amenity\"=\"ice_cream\"];
  relation(around:{ICECREAM_SEARCH_RADIUS_M},{lat},{lon})[\"amenity\"=\"ice_cream\"];
  node(around:{ICECREAM_SEARCH_RADIUS_M},{lat},{lon})[\"shop\"=\"ice_cream\"];
  way(around:{ICECREAM_SEARCH_RADIUS_M},{lat},{lon})[\"shop\"=\"ice_cream\"];
  relation(around:{ICECREAM_SEARCH_RADIUS_M},{lat},{lon})[\"shop\"=\"ice_cream\"];
);
out center;"""

    pois = []

    # Try primary server, then fallback
    for server_url in (PRIMARY_OVERPASS_URL, FALLBACK_OVERPASS_URL):
        data = _query_overpass(query, server_url)

        if not data:
            continue

        # Parse elements
        elements = data.get("elements", [])
        seen = set()

        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name", "Ice cream shop")
            lat_e = el.get("lat") or el.get("center", {}).get("lat")
            lon_e = el.get("lon") or el.get("center", {}).get("lon")

            if not lat_e or not lon_e:
                continue

            # Deduplicate
            key = (round(lat_e, 5), round(lon_e, 5), name)
            if key in seen:
                continue

            seen.add(key)
            pois.append({"name": name, "lat": lat_e, "lon": lon_e})

        # Success, break out
        break

    print(f"🍦 Ice cream POIs returned: {len(pois)}")
    return pois


def filter_chargers_by_icecream(
    chargers: List[dict], pois: List[dict], max_dist_m: float
) -> Tuple[List[dict], List[dict]]:
    """Filter chargers that have ice cream POIs within distance.

    Args:
        chargers: List of charger dicts
        pois: List of POI dicts
        max_dist_m: Maximum distance in meters

    Returns:
        (filtered_chargers, matching_pois): Subset of original lists
    """
    filtered = []
    matches = []

    for ch in chargers:
        for poi in pois:
            if (
                haversine(ch["lat"], ch["lon"], poi["lat"], poi["lon"])
                <= max_dist_m
            ):
                filtered.append(ch)
                matches.append(poi)
                break

    return filtered, matches
