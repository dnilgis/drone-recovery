import pandas as pd
import os
import re
import json
import random

# --- CONFIGURATION ---
SITE_NAME = "Direct Drone Recovery"
CONTACT_EMAIL = "your-email@example.com" # <--- Update this if you want!
INPUT_FILE = "drone_pilots_WITH_PHONES_FINAL.csv"
OUTPUT_DIR = "deploy_me"

# --- STATE GPS DATABASE (Keeps pins in USA) ---
state_centers = {
    'AL': '32.806671, -86.791130', 'AK': '61.370716, -152.404419', 'AZ': '33.729759, -111.431221',
    'AR': '34.969704, -92.373123', 'CA': '36.116203, -119.681564', 'CO': '39.059811, -105.311104',
    'CT': '41.597782, -72.755371', 'DE': '39.318523, -75.507141', 'DC': '38.897438, -77.026817',
    'FL': '27.766279, -81.686783', 'GA': '33.040619, -83.643074', 'HI': '21.094318, -157.498337',
    'ID': '44.240459, -114.478828', 'IL': '40.349457, -88.986137', 'IN': '39.849426, -86.258278',
    'IA': '42.011539, -93.210526', 'KS': '38.526600, -96.726486', 'KY': '37.668140, -84.670067',
    'LA': '31.169546, -91.867805', 'ME': '44.693947, -69.381927', 'MD': '39.063946, -76.802101',
    'MA': '42.230171, -71.530106', 'MI': '43.326618, -84.536095', 'MN': '45.694454, -93.900192',
    'MS': '32.741646, -89.678696', 'MO': '38.456085, -92.288368', 'MT': '46.921925, -110.454353',
    'NE': '41.125370, -98.268082', 'NV': '38.313515, -117.055374', 'NH': '43.452492, -71.563896',
    'NJ': '40.298904, -74.521011', 'NM': '34.840515, -106.248482', 'NY': '42.165726, -74.948051',
    'NC': '35.630066, -79.806419', 'ND': '47.528912, -99.784012', 'OH': '40.388783, -82.764915',
    'OK': '35.565342, -96.928917', 'OR': '44.572021, -122.070938', 'PA': '40.590752, -77.209755',
    'RI': '41.680893, -71.511780', 'SC': '33.856892, -80.945007', 'SD': '44.299782, -99.438828',
    'TN': '35.747845, -86.692345', 'TX': '31.054487, -97.563461', 'UT': '40.150032, -111.862434',
    'VT': '44.045876, -72.710686', 'VA': '37.769337, -78.169968', 'WA': '47.400902, -121.490494',
    'WV': '38.491226, -80.954453', 'WI': '44.268543, -89.616508', 'WY': '42.755966, -107.302490'
}

def clean_text(text):
    if pd.isna(text): return ""
    return str(text).strip()

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')

# --- SMART CATEGORY DETECTOR ---
def get_services(row):
    text = (str(row.get('Name', '')) + " " + str(row.get('Bio', ''))).lower()
    services = []
    
    # Keyword matching
    if any(x in text for x in ['deer', 'game', 'hunt', 'wildlife', 'buck']):
        services.append("Deer Recovery")
    if any(x in text for x in ['ag', 'farm', 'crop', 'seed', 'spray', 'field']):
        services.append("Agriculture")
    if any(x in text for x in ['photo', 'video', 'cinema', 'estate', 'survey', 'map']):
        services.append("Photography & Survey")
    if any(x in text for x in ['pet', 'dog', 'cat', 'animal']):
        services.append("Pet Recovery")
    if any(x in text for x in ['thermal', 'heat']):
        services.append("Thermal Imaging")
        
    if not services:
        return "General Drone Services"
    return ", ".join(services)

# --- MAIN BUILDER ---
def run_master_build():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: '{INPUT_FILE}' not found.")
        return

    print("Reading database...")
    df = pd.read_csv(INPUT_FILE)
    
    # 1. FIX COORDINATES (Force USA)
    print("Checking GPS coordinates...")
    if 'Coordinates' not in df.columns:
        df['Coordinates'] = "0,0"

    for index, row in df.iterrows():
        raw_coords = str(row.get('Coordinates', '0,0'))
        needs_fix = False
        
        if raw_coords == "0,0" or "," not in raw_coords:
            needs_fix = True
        else:
            try:
                lat, lng = map(float, raw_coords.split(','))
                if not (24 <= lat <= 50 and -125 <= lng <= -66): # USA Box
                    needs_fix = True
            except:
                needs_fix = True
        
        if needs_fix:
            state = str(row.get('State', '')).strip().upper()
            if state in state_centers:
                # Add random jitter
                base_lat, base_lng = state_centers[state].split(',')
                lat = float(base_lat) + random.uniform(-0.1, 0.1)
                lng = float(base_lng) + random.uniform(-0.1, 0.1)
                df.at[index, 'Coordinates'] = f"{lat}, {lng}"
    
    # Save fixed data back to CSV
    df.to_csv(INPUT_FILE, index=False)

    # 2. GENERATE WEBSITE
    print("Building Website with Features...")
    os.makedirs(f"{OUTPUT_DIR}/pilot", exist_ok=True)
    
    map_data = []
    
    for _, row in df.iterrows():
        try:
            coords = str(row.get('Coordinates', '0,0')).split(',')
            if len(coords) == 2:
                lat, lng = coords[0].strip(), coords[1].strip()
                name = clean_text(row.get('Name'))
                city = clean_text(row.get('City'))
                services = get_services(row)
                slug = slugify(f"{name}-{city}")
                
                pilot_info = {
                    "name": name,
                    "phone": clean_text(row.get('Found_Phone', 'Click for #')),
                    "lat": lat,
                    "lng": lng,
                    "services": services,
                    "url": f"pilot/{slug}.html"
                }
                map_data.append(pilot_info)
        except: continue

    js_array = json.dumps(map_data)

    index_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{SITE_NAME} | Find Local Drone Pilots</title>
        
        <meta name="description" content="Free directory of thermal drone pilots for deer recovery, agriculture, and photography. Find a pilot near you.">
        <meta property="og:title" content="{SITE_NAME} - Find a Pilot">
        <meta property="og:description" content="Map of local drone pilots for recovery and aerial services.">
        
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
            #map {{ height: 100vh; width: 100%; }}
            
            .info-box {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                position: absolute;
                top: 20px;
                right: 20px;
                z-index: 1000;
                width: 300px;
            }}
            
            h1 {{ margin: 0 0 10px; font-size: 1.5rem; color: #2c3e50; }}
            p {{ font-size: 0.9rem; color: #555; margin-bottom: 15px; }}
            
            /* CONTROLS */
            .control-group {{ margin-bottom: 10px; }}
            label {{ font-weight: bold; font-size: 0.8rem; display: block; margin-bottom: 5px; }}
            select {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
            
            /* BUTTONS */
            .btn {{ display: block; width: 100%; padding: 10px 0; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 10px; cursor: pointer; border: none; }}
            .btn-locate {{ background: #3498db; color: white; }}
            .btn-add {{ background: #27ae60; color: white; }}
            .btn:hover {{ opacity: 0.9; }}
            
            .pilot-count {{ background: #eee; padding: 5px; border-radius: 4px; font-size: 0.8rem; text-align: center; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="info-box">
            <h1>🦌 {SITE_NAME}</h1>
            <div class="pilot-count"><strong>{len(map_data)}</strong> Pilots Available</div>
            <p>Find thermal, ag, and photo drone pilots directly. No fees. No Middleman.</p>
            
            <div class="control-group">
                <label>Filter by Service:</label>
                <select id="serviceFilter" onchange="filterMap()">
                    <option value="All">Show All Services</option>
                    <option value="Deer Recovery">Deer Recovery</option>
                    <option value="Agriculture">Agriculture</option>
                    <option value="Photography">Photography</option>
                    <option value="Thermal">Thermal Imaging</option>
                </select>
            </div>

            <button class="btn btn-locate" onclick="locateUser()">📍 Find Near Me</button>
            <a href="mailto:{CONTACT_EMAIL}?subject=Add My Drone Business" class="btn btn-add">➕ Add Me to Map</a>
        </div>

        <div id="map"></div>
        
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            var map = L.map('map').setView([39.8283, -98.5795], 5);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ attribution: '© OpenStreetMap' }}).addTo(map);

            var allPilots = {js_array};
            var markers = [];

            function renderMap(pilots) {{
                markers.forEach(m => map.removeLayer(m));
                markers = [];
                pilots.forEach(p => {{
                    var marker = L.marker([p.lat, p.lng])
                        .bindPopup(`<b>${{p.name}}</b><br><span style="color:#666;font-size:0.9em">${{p.services}}</span><br><br><a href="${{p.url}}">View Profile</a>`);
                    marker.addTo(map);
                    markers.push(marker);
                }});
            }}

            renderMap(allPilots);

            function filterMap() {{
                var cat = document.getElementById('serviceFilter').value;
                if(cat === "All") {{ renderMap(allPilots); return; }}
                
                var filtered = allPilots.filter(p => p.services.includes(cat) || (cat === "Photography" && p.services.includes("Photo")));
                renderMap(filtered);
            }}

            function locateUser() {{
                if (!navigator.geolocation) {{ alert("Geolocation not supported"); return; }}
                navigator.geolocation.getCurrentPosition(pos => {{
                    var lat = pos.coords.latitude;
                    var lng = pos.coords.longitude;
                    map.flyTo([lat, lng], 9);
                    L.circleMarker([lat, lng], {{color: 'blue', radius: 10}}).addTo(map).bindPopup("You").openPopup();
                }}, () => alert("Location access denied."));
            }}
        </script>
    </body>
    </html>
    """
    
    with open(f"{OUTPUT_DIR}/index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    
    # 3. GENERATE PROFILES (SEO OPTIMIZED)
    print("Generating SEO Profile Pages...")
    for _, row in df.iterrows():
        name = clean_text(row.get('Name'))
        city = clean_text(row.get('City'))
        state = clean_text(row.get('State'))
        phone = clean_text(row.get('Found_Phone', 'Number Pending'))
        bio = clean_text(row.get('Bio'))
        services = get_services(row)
        slug = slugify(f"{name}-{city}")
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{name} - {services} in {city}, {state}</title>
            <meta name="description" content="Hire {name} for {services} in {city}, {state}. Direct phone: {phone}. No middleman fees.">
            <style>
                body {{ font-family: sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; line-height: 1.6; }}
                .card {{ border: 1px solid #ddd; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }}
                .btn {{ background: #27ae60; color: white; text-decoration: none; padding: 15px 30px; border-radius: 5px; font-size: 1.2rem; display: inline-block; margin-top: 15px; }}
                .tags {{ color: #555; font-style: italic; }}
            </style>
        </head>
        <body>
            <a href="../index.html">← Back to Map</a>
            <br><br>
            <div class="card">
                <h1>{name}</h1>
                <p>📍 {city}, {state}</p>
                <p class="tags">{services}</p>
                <p>{bio}</p>
                <a href="tel:{phone}" class="btn">📞 Call: {phone}</a>
            </div>
        </body>
        </html>
        """
        with open(f"{OUTPUT_DIR}/pilot/{slug}.html", "w", encoding="utf-8") as f:
            f.write(html)
            
    print("✅ MASTER BUILD COMPLETE.")

if __name__ == "__main__":
    run_master_build()