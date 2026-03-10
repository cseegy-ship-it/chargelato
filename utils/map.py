"""
Map creation and configuration module for the EV Charging Finder application.

This module provides functionality to create and customize Folium maps
for displaying the user's location and nearby points of interest.

Features:
- Creates interactive maps centered on searched locations
- Displays user location with blue circle markers
- Supports adding charger markers and ice cream locations
- Customizable marker styling with popups and tooltips

The maps are rendered in the Streamlit interface using st_folium.
"""

import folium


def create_map(lat, lon, place, chargers=None, icecreams=None):
    """
    Create an interactive Folium map with location marker, chargers and ice cream POIs.
    
    Args:
        lat (float): Latitude of the map center
        lon (float): Longitude of the map center
        place (str): Name of the searched location
        chargers (list, optional): List of charger dictionaries to display
        icecreams (list, optional): List of ice cream POI dictionaries to display
    
    Returns:
        folium.Map: Configured interactive map object
    """
    m = folium.Map(
        location=[lat, lon],
        zoom_start=14,
        control_scale=True
    )

    # user's location marker
    folium.CircleMarker(
        location=[lat, lon],
        radius=7,
        popup=folium.Popup(
            f"<div style='background-color: #0051BA; color: white; padding: 8px 12px; border-radius: 4px; font-weight: bold; text-align: center;'>{place or 'Default location'}</div>",
            max_width=250,
        ),
        tooltip=folium.Tooltip(place or 'Default location'),
        color="white",
        fill=True,
        fillColor="blue",
        fillOpacity=0.9,
        weight=3,
    ).add_to(m)

    # charger markers (no extras if list empty)
    if chargers:
        for ch in chargers:
            plug = ch.get("plug", "Unknown")
            power = ch.get("power")
            power_str = f"{power} kW" if power is not None else "N/A"
            tooltip_text = f"⚡ {ch['name']}\n🔌 {plug}\n⚡ {power_str}"
            folium.CircleMarker(
                location=[ch["lat"], ch["lon"]],
                radius=9,
                popup=folium.Popup(
                    f"⚡ {ch['name']}<br>🔌 {plug}<br>⚡ {power_str}",
                    max_width=200,
                ),
                tooltip=tooltip_text,
                color="white",
                fill=True,
                fillColor="green",
                fillOpacity=0.8,
                weight=2,
            ).add_to(m)

    # ice cream markers (yellow)
    if icecreams:
        for ic in icecreams:
            folium.CircleMarker(
                location=[ic["lat"], ic["lon"]],
                radius=7,
                popup=folium.Popup(f"🍦 {ic['name']}", max_width=200),
                tooltip=f"🍦 {ic['name']}",
                color="black",
                fill=True,
                fillColor="#FFDC00",
                fillOpacity=0.9,
                weight=2,
            ).add_to(m)

    return m