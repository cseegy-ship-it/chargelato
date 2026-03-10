import requests
import json

# Test the Open Charge Map API with Berlin coordinates
url = "https://api.openchargemap.io/v3/poi"
params = {
    "latitude": 52.48671,
    "longitude": 13.35544,
    "distance": 5,
    "distanceunit": "KM",
    "maxresults": 5
}

try:
    response = requests.get(url, params=params, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Number of results: {len(data) if isinstance(data, list) else 'Not a list'}")
        
        if isinstance(data, list) and len(data) > 0:
            print(f"\nFirst station keys: {list(data[0].keys())}")
            print(f"\nFirst station (partial - first 3 keys):")
            first_few = {k: data[0][k] for k in list(data[0].keys())[:3]}
            print(json.dumps(first_few, indent=2, default=str))
        else:
            print(f"Response type: {type(data)}")
            print(f"Response (first 500 chars): {str(data)[:500]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
