import streamlit as st
from streamlit_folium import st_folium

from config import DEFAULT_LAT, DEFAULT_LON
from ui.styles import apply_styles
from services.geocoding import get_coordinates
from services.chargers import get_chargers
from utils.map import create_map

# --- page setup ----------------------------------------------------------------
st.set_page_config(layout="wide")
apply_styles()
st.title("Chargelato ⚡🍦")

# --- user input ----------------------------------------------------------------
place = st.text_input("Search location")

# --- lookup --------------------------------------------------------------------
lat, lon = get_coordinates(place)
chargers = get_chargers(lat, lon)

# --- render --------------------------------------------------------------------
m = create_map(lat or DEFAULT_LAT, lon or DEFAULT_LON, place, chargers)
st_folium(m, use_container_width=True, height=600)
