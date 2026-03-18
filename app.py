"""
Main Streamlit application for EV Charging Finder with OCPI simulation.

Orchestrates:
- User input (location search, ice cream toggle)
- Map rendering with charger and POI markers
- API calls to charger and ice cream services
- Interactive OCPI API simulation (displays request/response cycle)

Features:
- Real-time location geocoding
- Nearby EV charger discovery
- Optional ice cream shop matching
- Animated OCPI terminal showing simulated API calls
"""

import html
import json
import re
import time
import unicodedata
from typing import Optional

import streamlit as st
from streamlit_folium import st_folium

from config import (
    DEFAULT_LAT,
    DEFAULT_LON,
    DEFAULT_CHARGER_RADIUS_KM,
    ICE_MODE_CHARGER_RADIUS_KM,
    DEFAULT_ICE_CREAM_RADIUS_M,
    MIN_ICE_CREAM_RADIUS_M,
    MAX_ICE_CREAM_RADIUS_M,
)
from ui.styles import apply_styles
from services.geocoding import get_coordinates
from services.chargers import get_chargers
from services.icecream import get_icecream_pois, filter_chargers_by_icecream
from utils.map import create_map

# --- OCPI Simulation Helpers ---------------------------------------------------


def _slugify_name(name: str) -> str:
    """Convert a charger name to a URL-safe slug using NFKD normalization.

    Examples:
        "Leberstraße" → "leberstrasse"
        "Foo Bar" → "foobar"
    """
    normalized = unicodedata.normalize("NFKD", name or "")
    slug = "".join(ch for ch in normalized if ch.isalnum())
    return slug.lower()


def _format_code_block(code: str) -> str:
    """Format code as a VS Code-style block with line numbers and syntax highlighting.

    Applies coloring to:
    - HTTP verbs (GET)
    - Header names (Authorization, Content-Type)
    - JSON keys and values
    """
    escaped = html.escape(code)

    # HTTP verb coloring
    escaped = escaped.replace(
        "GET ",
        "<span style='color:#3fb950; font-weight: 600'>GET</span> ",
    )

    # Header coloring
    escaped = escaped.replace(
        "Authorization:",
        "<span style='color:#79c0ff'>Authorization:</span>",
    )
    escaped = escaped.replace(
        "Content-Type:",
        "<span style='color:#79c0ff'>Content-Type:</span>",
    )

    # JSON key coloring: "key" :
    escaped = re.sub(
        r'(&quot;[^&quot;]+&quot;)(\s*):',
        r"<span style='color:#79c0ff'>\1</span>\2:",
        escaped,
    )

    # JSON string value coloring: : "string"
    escaped = re.sub(
        r':\s*(&quot;[^&quot;]*&quot;)',
        r": <span style='color:#ffa657'>\1</span>",
        escaped,
    )

    # JSON numeric value coloring: : 123
    escaped = re.sub(
        r':\s*([0-9]+)',
        r": <span style='color:#a5d6ff'>\1</span>",
        escaped,
    )

    # Add line numbers
    lines = escaped.split("\n")
    formatted_lines = [
        f"<span style='color:#6e7681'>{i:02d}</span>  {line}"
        for i, line in enumerate(lines, start=1)
    ]
    formatted_code = "<br>".join(formatted_lines)

    return f"""
    <div style="
        background-color: #0d1117;
        color: #c9d1d9;
        padding: 20px;
        border-radius: 10px;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        overflow-x: auto;
    ">
    {formatted_code}
    </div>
    """


def _render_terminal(code: str) -> None:
    """Display code in a styled terminal block."""
    st.markdown(_format_code_block(code), unsafe_allow_html=True)


def build_ocpi_call(charger: dict) -> tuple[str, dict]:
    """Build a simulated OCPI GET request and its JSON response.

    Args:
        charger: Charger dictionary with keys: name, plug, power, lat, lon

    Returns:
        (request_text, response_json): HTTP request string and response dict
    """
    name = charger.get("name", "")
    plug = charger.get("plug")
    power_kw = charger.get("power") or 0
    power_watts = int(power_kw * 1000) if isinstance(power_kw, (int, float)) else 0

    # Generate location ID from charger name
    location_id = _slugify_name(name)
    location_id = f"LOC-{location_id}" if location_id else "LOC-UNKNOWN"

    # Build request line
    request_url = f"https://api.partner-network.com/ocpi/2.2.1/locations/DE/ABC/{location_id}"
    auth_token = "VIRTATOKEN-9f3a2c7e-4b8d-11ec-81d3-0242ac130003"
    request_text = (
        f"GET {request_url}\n"
        f"Authorization: Token {auth_token}\n"
        "Content-Type: application/json"
    )

    # Determine connector type
    connector_standard = "IEC_62196_T2" if "Type 2" in (plug or "") else "UNKNOWN"

    # Build OCPI response
    response = {
        "status_code": 1000,
        "status_message": "Success",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "data": [
            {
                "id": location_id,
                "name": name,
                "country_code": "DE",
                "party_id": "ABC",
                "evses": [
                    {
                        "uid": "EVSE-1",
                        "status": "AVAILABLE",
                        "connectors": [
                            {
                                "standard": connector_standard,
                                "max_electric_power": power_watts,
                            }
                        ],
                    }
                ],
            }
        ],
    }

    return request_text, response


def _get_clicked_charger(chargers: list[dict], click: dict) -> Optional[dict]:
    """Match a clicked map point to a charger.

    Folium returns lat/lon of the last clicked object. This matches it to
    the closest charger in the list (within tolerance, or nearest if no exact match).

    Args:
        chargers: List of charger dictionaries
        click: Click event data from folium (contains lat, lon, etc.)

    Returns:
        Matched charger dict, or None if no chargers or invalid click data
    """
    if not (click and chargers):
        return None

    lat = click.get("lat") or click.get("latitude")
    lon = click.get("lng") or click.get("lon") or click.get("longitude")
    if lat is None or lon is None:
        return None

    # Try exact match with tolerance for floating point
    tol = 1e-4
    for ch in chargers:
        if ch.get("lat") is None or ch.get("lon") is None:
            continue
        if abs(ch["lat"] - lat) < tol and abs(ch["lon"] - lon) < tol:
            return ch

    # Fall back to nearest charger
    closest = min(
        chargers,
        key=lambda c: (c.get("lat", 0) - lat) ** 2 + (c.get("lon", 0) - lon) ** 2,
    )
    return closest


def _init_ocpi_session_state() -> None:
    """Initialize OCPI simulation state in Streamlit session."""
    if "selected_charger" not in st.session_state:
        st.session_state.selected_charger = None
    if "ocpi_phase" not in st.session_state:
        st.session_state.ocpi_phase = None
    if "ocpi_start_time" not in st.session_state:
        st.session_state.ocpi_start_time = None


def _init_ice_query_session_state() -> None:
    """Initialize ice cream query caching in Streamlit session."""
    if "last_ice_query" not in st.session_state:
        st.session_state.last_ice_query = None
        st.session_state.ice_pois = []



# --- Page Setup ----------------------------------------------------------------
st.set_page_config(layout="wide")
apply_styles()
st.title("Chargelato ⚡🍦")

# --- User Input ----------------------------------------------------------------
place = st.text_input("Search location")
col1, col2 = st.columns([1, 2])
with col1:
    ice_mode = st.checkbox("🍦 Find ice cream while charging")
with col2:
    ice_dist = st.slider(
        "🍦 Max walking distance (m)",
        min_value=MIN_ICE_CREAM_RADIUS_M,
        max_value=MAX_ICE_CREAM_RADIUS_M,
        value=DEFAULT_ICE_CREAM_RADIUS_M,
        step=50,
        disabled=not ice_mode,
    )

# --- Lookup Data ---------------------------------------------------------------
# Geocode location
lat, lon = get_coordinates(place)

# Determine charger search radius
radius = (
    ICE_MODE_CHARGER_RADIUS_KM if ice_mode else DEFAULT_CHARGER_RADIUS_KM
)
chargers = get_chargers(lat, lon, radius_km=radius)

# Fetch and filter ice cream POIs if mode is enabled
ice_pois = []
if ice_mode:
    _init_ice_query_session_state()

    query_key = (lat, lon, ice_dist)
    if st.session_state.last_ice_query != query_key:
        # Query only when location or radius changes
        try:
            with st.spinner("🍦 Fetching ice cream shops..."):
                st.session_state.last_ice_query = query_key
                st.session_state.ice_pois = get_icecream_pois(lat, lon, ice_dist)
        except Exception as e:
            print(f"⚠️  Error fetching ice cream POIs: {e}")
            st.session_state.ice_pois = []

    ice_pois = st.session_state.ice_pois
    if chargers and ice_pois:
        chargers, ice_pois = filter_chargers_by_icecream(
            chargers, ice_pois, ice_dist
        )
else:
    # Clear cached POIs when mode is disabled
    _init_ice_query_session_state()
    st.session_state.last_ice_query = None
    st.session_state.ice_pois = []

# --- Render Map ----------------------------------------------------------------
m = create_map(lat or DEFAULT_LAT, lon or DEFAULT_LON, place, chargers, icecreams=ice_pois)
map_data = st_folium(m, use_container_width=True, height=600)

# --- OCPI Simulation -----------------------------------------------------------
_init_ocpi_session_state()

# Detect charger clicks and start simulation
if map_data and map_data.get("last_object_clicked"):
    clicked = map_data["last_object_clicked"]
    clicked_charger = _get_clicked_charger(chargers, clicked)

    if clicked_charger:
        previous = st.session_state.selected_charger
        is_new_charger = (
            not previous
            or previous.get("lat") != clicked_charger.get("lat")
            or previous.get("lon") != clicked_charger.get("lon")
        )

        if is_new_charger:
            st.session_state.selected_charger = clicked_charger
            st.session_state.ocpi_phase = "request"
            st.session_state.ocpi_start_time = time.time()

# Render OCPI simulation if charger is selected
selected = st.session_state.get("selected_charger")
if selected:
    now = time.time()
    start = st.session_state.get("ocpi_start_time") or now
    elapsed = now - start

    # Determine current phase
    if elapsed < 5:
        phase = "request"
    elif elapsed < 7:
        phase = "loading"
    else:
        phase = "response"

    st.session_state.ocpi_phase = phase
    request_text, response = build_ocpi_call(selected)

    # Display header and terminal
    st.markdown("### ⚡ OCPI API Call Simulation")

    if phase == "request":
        _render_terminal(request_text)
    elif phase == "loading":
        # Render loading message with yellow styling (no line numbers needed)
        st.markdown(
            """
            <div style="
                background-color: #0d1117;
                color: #e3b341;
                padding: 20px;
                border-radius: 10px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
            ">
            Fetching data from OCPI...
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        _render_terminal(json.dumps(response, indent=2))

    # Continue animation until response phase ends
    if elapsed < 7:
        time.sleep(0.5)
        st.rerun()
