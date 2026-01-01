import pandas as pd
import os
import re
import json

# CONFIGURATION
SITE_NAME = "Direct Drone Recovery"
DOMAIN = "https://dnilgis.github.io/drone-recovery" 
INPUT_FILE = "drone_pilots_WITH_PHONES_FINAL.csv"
OUTPUT_DIR = "deploy_me"

def clean_text(text):
    if pd.isna(text): return ""
    return str(text).strip()

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')

def build_website():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Missing '{INPUT_FILE}'.")
        return

    print("Reading database...")
    df = pd.read_csv(INPUT_FILE)
    
    os.makedirs(f"{OUTPUT_DIR}/pilot", exist_ok=True)
    
    # --- STEP 1: GENERATE MAP DATA ---
    print("Building Homepage...")
    
    map_data = []
    for _, row in df.iterrows():
        try:
            coords = str(row.get('Coordinates', '0,0')).split(',')
            if len(coords) == 2 and coords[0].strip() != '0':
                lat, lng = coords[0].strip(), coords[1].strip()
                name = clean_text(row.get('Name'))
                city = clean_text(row.get('City'))
                slug = slugify(f"{name}-{city}")
                
                pilot_info = {
                    "name": name,
                    "phone": clean_text(row.get('Found_Phone', 'Click Profile')),
                    "lat": lat,
                    "lng": lng,
                    "url": f"pilot/{slug}.html"
                }
                map_data.append(pilot_info)
        except: continue

    # SAFE JSON CONVERSION (This fixes the apostrophe crash)
    js_array = json.dumps(map_data)

    index_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{SITE_NAME}</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            body {{ margin: 0; font-family: sans-serif; }}
            #map {{ height: 100vh; width: 100%; }}
            .info-box {{ background: white; padding: 10px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.2); position: absolute; top: 10px; right: 10px; z-index: 1000; max-width: 300px; }}
        </style>
    </head>
    <body>
        <div class="info-box">
            <h1>🦌 {SITE_NAME}</h1>
            <p><strong>{len(map_data)} Pilots Found</strong></p>
        </div>
        <div id="map"></div>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            var map = L.map('map').setView([39.8283, -98.5795], 5);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap'
            }}).addTo(map);

            var pilots = {js_array};

            pilots.forEach(p => {{
                L.marker([p.lat, p.lng]).addTo(map)
                    .bindPopup(`<b>${{p.name}}</b><br><a href="${{p.url}}">View Profile</a>`);
            }});
        </script>
    </body>
    </html>
    """
    
    with open(f"{OUTPUT_DIR}/index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    
    # --- STEP 2: GENERATE PROFILES ---
    print("Building Profiles...")
    for _, row in df.iterrows():
        name = clean_text(row.get('Name'))
        city = clean_text(row.get('City'))
        state = clean_text(row.get('State'))
        phone = clean_text(row.get('Found_Phone', 'Number Pending'))
        slug = slugify(f"{name}-{city}")
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{name}</title></head>
        <body style="font-family:sans-serif; padding:20px; text-align:center;">
            <a href="../index.html">← Back to Map</a>
            <h1>{name}</h1>
            <p>📍 {city}, {state}</p>
            <a href="tel:{phone}" style="background:#27ae60; color:white; padding:15px; text-decoration:none; display:inline-block; border-radius:5px; font-size:1.2rem;">📞 Call: {phone}</a>
        </body>
        </html>
        """
        with open(f"{OUTPUT_DIR}/pilot/{slug}.html", "w", encoding="utf-8") as f:
            f.write(html)

    print("✅ SITE BUILT SUCCESSFULLY.")

if __name__ == "__main__":
    build_website()