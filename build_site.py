import csv
import os
import re
import json
import random
from datetime import datetime

# --- CONFIGURATION ---
DB_FILE = "drone_pilots_WITH_PHONES_FINAL" 
if not os.path.exists(DB_FILE) and os.path.exists(DB_FILE + ".csv"):
    DB_FILE = DB_FILE + ".csv"

BRAND_NAME = "Direct Drone Recovery"
TAGLINE = "Find thermal, ag, and photo drone pilots directly. No fees. No Middleman."
DOMAIN = "https://dnilgis.github.io/drone-recovery" 

def clean_slug(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def get_jitter():
    # This provides the "clustered away from each other" swarm look
    return random.uniform(-0.04, 0.04)

# --- LIGHT THEME TEMPLATE (DEER REMOVED) ---
index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{brand} | Find Local Drone Pilots</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <style>
        body, html {{ margin: 0; padding: 0; height: 100%; font-family: sans-serif; overflow: hidden; }}
        #map {{ height: 100vh; width: 100vw; z-index: 1; }}
        .info-box {{
            position: absolute; top: 20px; right: 20px; width: 300px;
            background: rgba(255, 255, 255, 0.95); padding: 20px;
            border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            z-index: 1000; border: 1px solid #e0e0e0;
        }}
        .info-box h1 {{ margin: 0 0 5px 0; font-size: 1.2rem; color: #333; font-weight: bold; }}
        .pilot-count {{ font-weight: bold; color: #333; display: block; margin: 10px 0; text-align: center; font-size: 0.85rem; }}
        .btn {{
            display: block; width: 100%; padding: 12px 0; margin-bottom: 10px;
            border-radius: 4px; font-weight: bold; text-align: center;
            text-decoration: none; font-size: 0.9rem;
        }}
        .btn-blue {{ background: #3b82f6; color: white; }}
        .btn-green {{ background: #10b981; color: white; }}
    </style>
</head>
<body>
<div class="info-box">
    <h1>{brand}</h1>
    <span class="pilot-count">{count} Pilots Available</span>
    <p style="font-size:0.8rem; color:#666; line-height:1.4;">{tagline}</p>
    
    <select style="width:100%; padding:10px; margin-bottom:15px; border-radius:4px; border:1px solid #ccc;">
        <option>Show All Services</option>
        <option>Thermal Recovery</option>
        <option>Agriculture</option>
    </select>
    <a href="#" class="btn btn-blue" onclick="alert('Locating...');">📍 Find Near Me</a>
    <a href="join.html" class="btn btn-green">➕ Add Me To Map</a>
</div>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    var map = L.map('map', {{ zoomControl: false }}).setView([39.8283, -98.5795], 5);
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
    var pilots = {json_data};
    var quadIcon = L.divIcon({{
        className: 'drone-icon',
        html: `<svg viewBox="0 0 24 24" width="24" height="24" fill="#3b82f6"><path d="M21 16.5c0 .38-.21.71-.53.88l-7.97 4.43c-.16.09-.33.14-.5.14s-.34-.05-.5-.14l-7.97-4.43c-.32-.17-.53-.5-.53-.88V7.5c0-.38.21-.71.53-.88l7.97-4.43c.16-.09.33-.14.5-.14s.34.05.5.14l7.97 4.43c.32.17.53.5.53.88v9z"/></svg>`,
        iconSize: [24, 24], iconAnchor: [12, 12]
    }});
    pilots.forEach(p => {{
        L.marker([p.lat, p.lng], {{icon: quadIcon}}).addTo(map).bindPopup('<b>'+p.name+'</b><br>'+p.city+', '+p.state+'<br><a href="'+p.url+'">Details</a>');
    }});
</script>
</body>
</html>
"""

def run_build():
    if not os.path.exists("pilot"): os.makedirs("pilot")
    map_data = []
    with open(DB_FILE, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            f, l = row.get('First Name', '').strip(), row.get('Last Name', '').strip()
            name, city, state = f"{f} {l}", row.get('city', '').strip(), row.get('state', '').strip()
            slug = clean_slug(f"{name}-{city}-{state}")
            url = f"pilot/{slug}.html"
            lat, lng = row.get('latitude'), row.get('longitude')
            if lat and lng and str(lat) != 'nan' and str(lat) != '':
                # FIXED: Corrected syntax to fix 'unhashable type' error
                map_data.append({"name": name, "lat": float(lat)+get_jitter(), "lng": float(lng)+get_jitter(), "city": city, "state": state, "url": url})

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html.format(brand=BRAND_NAME, tagline=TAGLINE, count=len(map_data), json_data=json.dumps(map_data)))
    print(f"SUCCESS: {len(map_data)} Pilots mapped with Swarm Jitter and no deer icon.")

if __name__ == "__main__":
    run_build()