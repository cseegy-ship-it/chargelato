import streamlit as st
from streamlit_folium import st_folium

from config import (
    DEFAULT_LAT,
    DEFAULT_LON,
    DEFAULT_CHARGER_RADIUS_KM,
    ICE_MODE_CHARGER_RADIUS_KM,
    ICE_CREAM_MATCH_RADIUS_M,
    DEFAULT_ICE_CREAM_RADIUS_M,
    MIN_ICE_CREAM_RADIUS_M,
    MAX_ICE_CREAM_RADIUS_M,
)
from ui.styles import apply_styles
from services.geocoding import get_coordinates
from services.chargers import get_chargers
from services.icecream import get_icecream_pois, filter_chargers_by_icecream
from utils.map import create_map

# --- page setup ----------------------------------------------------------------
st.set_page_config(layout="wide")
apply_styles()
st.title("Chargelato ⚡🍦")

# --- user input ----------------------------------------------------------------
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

# --- lookup --------------------------------------------------------------------
lat, lon = get_coordinates(place)
# choose radius based on ice cream toggle
radius = ICE_MODE_CHARGER_RADIUS_KM if ice_mode else DEFAULT_CHARGER_RADIUS_KM
chargers = get_chargers(lat, lon, radius_km=radius)

ice_pois = []
# avoid re-running Overpass on every rerun/interaction
if ice_mode:
    query_key = (lat, lon, ice_dist)
    if "last_ice_query" not in st.session_state:
        st.session_state.last_ice_query = None
        st.session_state.ice_pois = []
    if st.session_state.last_ice_query != query_key:
        # only call service when location or radius changes
        try:
            with st.spinner("🍦 Fetching ice cream shops..."):
                st.session_state.last_ice_query = query_key
                st.session_state.ice_pois = get_icecream_pois(lat, lon, ice_dist)
        except Exception:
            st.session_state.ice_pois = []

    ice_pois = st.session_state.ice_pois
    if chargers and ice_pois:
        chargers, ice_pois = filter_chargers_by_icecream(chargers, ice_pois, ice_dist)
else:
    # clear cached pois when mode is off to free memory
    st.session_state.last_ice_query = None
    st.session_state.ice_pois = []

# --- render --------------------------------------------------------------------
m = create_map(lat or DEFAULT_LAT, lon or DEFAULT_LON, place, chargers, icecreams=ice_pois)
st_folium(m, use_container_width=True, height=600)
