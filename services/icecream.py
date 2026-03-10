"""
Ice cream points-of-interest service for the EV Charging Finder application.

This module queries the Overpass API for ice cream shops (amenity=ice_cream)
near a given latitude/longitude.  It provides raw POI extraction plus a
helper to filter charger lists based on proximity to ice cream locations.

The primary functions are:

* get_icecream_pois(lat, lon, radius_m) -> list of POI dicts
* filter_chargers_by_icecream(chargers, pois, max_dist_m) -> (filtered, matches)

A simple haversine formula is used for distance computations; no external
dependencies are required.
"""

import math
import time
import requests
import streamlit as st

from config import OVERPASS_TIMEOUT_SECONDS, REQUEST_TIMEOUT, ICE_CREAM_MATCH_RADIUS_M, ICECREAM_SEARCH_RADIUS_M

PRIMARY_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
FALLBACK_OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"


def haversine(lat1, lon1, lat2, lon2):
    """Return distance in meters between two lat/lon points."""
    R = 6371000  # earth radius meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@st.cache_data(ttl=600, show_spinner=False)
def get_icecream_pois(lat, lon, radius_m):
    """Fetch nearby ice cream shops using Overpass.

    Caching ensures the same location/radius pair is only queried once every
    ten minutes.  The function also implements retry logic for 504 errors and
    can fall back to a secondary server if the primary is unavailable.

    Returns a list of dicts with keys ``name``, ``lat`` and ``lon``.
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
    # try primary then fallback
    for server_url in (PRIMARY_OVERPASS_URL, FALLBACK_OVERPASS_URL):
        print("🌍 Overpass server:", server_url)
        try:
            resp = requests.post(server_url, data=query, timeout=30)
        except requests.RequestException as e:
            print("⚠️ Overpass request exception", e)
            continue

        print("🍦 Overpass status:", resp.status_code)
        # retry once on gateway timeout
        if resp.status_code == 504:
            print("🍦 504 received, retrying after delay")
            time.sleep(2)
            try:
                resp = requests.post(server_url, data=query, timeout=30)
            except requests.RequestException as e:
                print("⚠️ Overpass retry exception", e)
                continue
            print("🍦 Overpass status (retry):", resp.status_code)

        if resp.status_code != 200:
            print("⚠️ Overpass API request failed")
            print("⚠️ Response preview:", resp.text[:300])
            # if we were on primary, loop will try fallback next
            continue

        # good response, parse and break out
        try:
            elements = resp.json().get("elements", [])
        except ValueError:
            print("⚠️ Overpass JSON parsing failed")
            return []

        seen = set()
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name", "Ice cream shop")
            lat_e = el.get("lat") or el.get("center", {}).get("lat")
            lon_e = el.get("lon") or el.get("center", {}).get("lon")
            if not lat_e or not lon_e:
                continue
            key = (round(lat_e, 5), round(lon_e, 5), name)
            if key in seen:
                continue
            seen.add(key)
            pois.append({"name": name, "lat": lat_e, "lon": lon_e})
        # break since we succeeded
        break

    print("🍦 Ice cream POIs returned:", len(pois))
    return pois

def filter_chargers_by_icecream(chargers, pois, max_dist_m):
    """Return subset of chargers that have an ice cream POI within ``max_dist_m``.

    Also return the list of matching POIs (duplicates removed).
    """
    filtered = []
    matches = []
    for ch in chargers:
        for poi in pois:
            if haversine(ch["lat"], ch["lon"], poi["lat"], poi["lon"]) <= max_dist_m:
                filtered.append(ch)
                matches.append(poi)
                break
    return filtered, matches