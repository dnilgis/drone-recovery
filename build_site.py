import csv
import os
import shutil
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
    return random.uniform(-0.04, 0.04)

# --- MAP TEMPLATE (Top-Right Info Box & Light Theme) ---
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

        .info-box h1 {{ margin: 0 0 5px 0; font-size: 1.2rem; color: #333; display: flex; align-items: center; gap: 8px; }}
        .pilot-count {{ font-weight: bold; color: #333; display: block; margin: 5px 0 15px 0; text-align: center; font-size: 0.85rem; }}

        .service-select {{ width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; margin-bottom: 15px; font-size: 0.9rem; color: #444; }}

        .btn {{
            display: block; width: 100%; padding: 12px 0; margin-bottom: 10px;
            border-radius: 4px; font-weight: bold; text-align: center;
            text-decoration: none; font-size: 0.9rem; border: none; cursor: pointer;
        }}
        .btn-blue {{ background: #3b82f6; color: white; }}
        .btn-green {{ background: #10b981; color: white; }}
        
        @media (max-width: 600px) {{ .info-box {{ width: calc(100% - 40px); top: 10px; right: 20px; }} }}
    </style>
</head>
<body>
<div class="info-box">
    <h1>🦌 {brand}</h1>
    <span class="pilot-count">{count} Pilots Available</span>
    <p style="font-size:0.8rem; color:#666; line-height:1.4;">{tagline}</p>
    
    <label style="font-size:0.75rem; font-weight:bold; color:#555;">Filter by Service:</label>
    <select class="service-select" id="serviceFilter">
        <option>Show All Services</option>
        <option>Thermal Recovery</option>
        <option>Agriculture</option>
        <option>Photo/Video</option>
    </select>

    <a href="#" class="btn btn-blue" onclick="alert('Locating...'); return false;">📍 Find Near Me</a>
    <a href="join.html" class="btn btn-green">➕ Add Me To Map</a>
</div>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    var map = L.map('map', {{ zoomControl: false }}).setView([39.8283, -98.5795], 5);
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
    var pilots = {json_data};
    pilots.forEach(p => {{
        L.marker([p.lat, p.lng]).addTo(map).bindPopup('<b>'+p.name+'</b><br>'+p.city+', '+p.state+'<br><a href="'+p.url+'">Details</a>');
    }});
</script>
</body>
</html>
"""

# --- JOIN PAGE TEMPLATE ---
join_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Get Listed | {brand}</title>
    <style>
        body {{ font-family: sans-serif; background: #f8f9fc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
        .card {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); max-width: 500px; text-align: center; }}
        h1 {{ font-size: 1.8rem; color: #333; margin-bottom: 20px; }}
        p {{ color: #666; line-height: 1.6; margin-bottom: 30px; }}
        .email-box {{ background: #effaf3; padding: 15px; border-radius: 6px; border: 1px solid #dcfce7; color: #166534; font-weight: bold; margin-bottom: 20px; }}
        .btn-green {{ display: block; background: #10b981; color: white; padding: 15px; border-radius: 6px; text-decoration: none; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="card">
        <span style="font-size: 3rem; color: #8b5cf6;">➕</span>
        <h1>Get Listed on the Map</h1>
        <p>We are building the largest directory of verified drone pilots. To add your business, please email us with your <b>Name, City, and Phone Number</b>.</p>
        <div class="email-box">ops@uniteddroneops.com</div>
        <a href="mailto:ops@uniteddroneops.com" class="btn-green">Click to Email Us</a>
        <a href="index.html" style="display:block; margin-top:20px; color:#999; text-decoration:none; font-size:0.9rem;">&larr; Back to Map</a>
    </div>
</body>
</html>
"""

# --- PILOT PROFILE TEMPLATE ---
profile_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{name} | {brand}</title>
    <style>
        body {{ font-family: sans-serif; background: #f4f4f9; display: flex; justify-content: center; padding: 40px; }}
        .card {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; width: 100%; border-top: 8px solid #3b82f6; }}
        h1 {{ margin: 0; color: #333; }}
        .phone {{ font-size: 1.5rem; font-weight: bold; color: #3b82f6; text-decoration: none; display: block; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>{name}</h1>
        <p>{city}, {state}</p>
        <div style="margin: 20px 0; line-height: 1.6; color: #555;">{bio}</div>
        <a href="tel:{phone}" class="phone">Call Direct: {phone}</a>
        <a href="../index.html" style="color:#666; text-decoration:none;">&larr; Back to Map</a>
    </div>
</body>
</html>
"""

def run_build():
    print("--- BUILDING DIRECT DRONE RECOVERY ENGINE ---")
    if not os.path.exists("pilot"): os.makedirs("pilot")
    map_data = []
    
    try:
        with open(DB_FILE, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                f, l = row.get('First Name', '').strip(), row.get('Last Name', '').strip()
                name, city, state = f"{f} {l}", row.get('city', '').strip(), row.get('state', '').strip()
                phone, bio = row.get('Phone', '').strip(), row.get('Bio', 'Verified professional pilot.')
                
                slug = clean_slug(f"{name}-{city}-{state}")
                url = f"pilot/{slug}.html"
                lat, lng = row.get('latitude'), row.get('longitude')
                
                if lat and lng and str(lat) != 'nan' and str(lat) != '':
                    # Fixed data structure to prevent TypeError
                    map_data.append({
                        "name": name, 
                        "lat": float(lat) + get_jitter(), 
                        "lng": float(lng) + get_jitter(), 
                        "city": city, 
                        "state": state, 
                        "url": url
                    })

                with open(url, "w", encoding="utf-8") as p:
                    p.write(profile_template.format(name=name, city=city, state=state, brand=BRAND_NAME, bio=bio, phone=phone))

        # Generate Home Page
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(index_html.format(brand=BRAND_NAME, tagline=TAGLINE, count=len(map_data), json_data=json.dumps(map_data)))

        # Generate Join Page
        with open("join.html", "w", encoding="utf-8") as j:
            j.write(join_html.format(brand=BRAND_NAME))

        print(f"--- SUCCESS: {len(map_data)} PILOTS GENERATED ---")

    except Exception as e:
        print(f"Build failed with error: {e}")

if __name__ == "__main__": 
    run_build()