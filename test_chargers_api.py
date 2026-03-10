#!/usr/bin/env python3
"""
Test script to verify Open Charge Map API connector type extraction.
"""

import requests
from config import OPEN_CHARGE_MAP_URL, OPEN_CHARGE_MAP_KEY

# Berlin coordinates
lat, lon = 52.48671, 13.35544
radius_km = 5

params = {
    "key": OPEN_CHARGE_MAP_KEY,
    "latitude": lat,
    "longitude": lon,
    "distance": radius_km,
    "distanceunit": "KM",
    "maxresults": 3,
    "compact": False,
    "verbose": False,
}

print("🔎 Fetching chargers from Open Charge Map API...")
resp = requests.get(OPEN_CHARGE_MAP_URL, params=params, timeout=15)

if resp.status_code != 200:
    print(f"❌ API Error: {resp.status_code}")
    exit(1)

data = resp.json()
print(f"✅ Received {len(data)} chargers\n")

# Inspect first 3 chargers
for i, poi in enumerate(data[:3]):
    print(f"\n--- Charger {i+1} ---")
    addr = poi.get("AddressInfo", {})
    print(f"Name: {addr.get('Title', 'N/A')}")
    print(f"Lat: {addr.get('Latitude', 'N/A')}")
    print(f"Lon: {addr.get('Longitude', 'N/A')}")
    
    connections = poi.get("Connections", [])
    print(f"Number of connections: {len(connections)}")
    
    if connections:
        conn = connections[0]
        print(f"  Power: {conn.get('PowerKW', 'N/A')} kW")
        print(f"  Full connection object: {conn}")
        
        conn_type = conn.get("ConnectionType", {})
        print(f"  ConnectionType: {conn_type}")
        plug = conn_type.get("Title", "Unknown") if isinstance(conn_type, dict) else "Unknown"
        print(f"  Extracted plug type: {plug}")
