import pandas as pd
import os
import re
import json

# CONFIGURATION
SITE_NAME = "Direct Drone Recovery"
# CONTACT EMAIL (Pilots will click this to email you)
CONTACT_EMAIL = "your-email@example.com" 

INPUT_FILE = "drone_pilots_WITH_PHONES_FINAL.csv"
OUTPUT_DIR = "deploy_me"

def clean_text(text):
    if pd.isna(text): return ""
    return str(text).strip()

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')

# SMART CATEGORY GUESSER
def guess_category(name, bio):
    text = (str(name) + " " + str(bio)).lower()
    if any(x in text for in ['deer', 'recovery', 'game', 'hunt', 'thermal', 'find']):
        return "Deer Recovery"
    if any(x in text for in ['ag', 'farm', 'crop', 'spray', 'seed']):
        return "Agriculture"
    if any(x in text for in ['photo', 'media', 'cinema', 'real estate', 'survey']):
        return "Photography/Survey"
    return "General Drone Services"

def build_website():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Missing '{INPUT_FILE}'.")
        return

    print("Reading database...")
    df = pd.read_csv(INPUT_FILE)
    
    os.makedirs(f"{OUTPUT_DIR}/pilot", exist_ok=True)
    
    # --- STEP 1: GENERATE MAP DATA ---
    print("Building Map & Filters...")
    
    map_data = []
    categories = {"All Services"} # Set ensures unique values

    for _, row in df.iterrows():
        try:
            coords = str(row.get('Coordinates', '0,0')).split(',')
            if len(coords) == 2 and coords[0].strip() != '0':
                lat, lng = coords[0].strip(), coords[1].strip()
                name = clean_text(row.get('Name'))
                city = clean_text(row.get('City'))
                # Guess category based on name
                category = guess_category(name, row.get('Bio', ''))
                categories.add(category)
                
                slug = slugify(f"{name}-{city}")
                
                pilot_info = {
                    "name": name,
                    "phone": clean_text(row.get('Found_Phone', 'Click Profile')),
                    "lat": lat,
                    "lng": lng,
                    "category": category,
                    "url": f"pilot/{slug}.html"
                }
                map_data.append(pilot_info)
        except: continue

    js_array = json.dumps(map_data)
    
    # Generate Category Options for HTML
    filter_options = ""
    for cat in sorted(list(categories)):
        if cat != "All Services":
            filter_options += f'<option value="{cat}">{cat}</option>'

    index_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{SITE_NAME} - Find a Pilot</title>
        <meta name="description" content="Find local drone pilots for deer recovery, agriculture, photography and more. Direct phone numbers, no fees.">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            body {{ margin: 0; font-family: sans-serif; }}
            #map {{ height: 100vh; width: 100%; }}
            
            /* FLOATING CONTROL PANEL */
            .info-box {{ 
                background: white; 
                padding: 15px; 
                border-radius: 8px; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.3); 
                position: absolute; 
                top: 10px; 
                right: 10px; 
                z-index: 1000; 
                max-width: 300px; 
            }}
            
            h1 {{ margin: 0 0 5px; font-size: 1.4rem; color: #2c3e50; }}
            p {{ margin: 0 0 10px; color: #666; font-size: 0.9rem; }}
            
            .stats {{ font-weight: bold; color: #27ae60; margin-bottom: 10px; display: block; }}
            
            /* FILTER DROPDOWN */
            select {{
                width: 100%;
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 4px;
                border: 1px solid #ddd;
                font-size: 1rem;
            }}

            /* BUTTONS */
            .btn {{ 
                display: block; 
                width: 90%; 
                padding: 10px; 
                text-align: center; 
                text-decoration: none; 
                border-radius: 5px; 
                margin-top: 5px; 
                font-weight: bold;
                margin: 5px auto;
            }}
            .btn-add {{ background: #34495e; color: white; font-size: 0.9rem; }}
            .btn-locate {{ background: #3498db; color: white; }}
            
            .btn:hover {{ opacity: 0.9; }}
        </style>
    </head>
    <body>
        <div class="info-box">
            <h1>🦌 Direct Drone Recovery</h1>
            <p>The free directory for thermal, ag, and photography drones. Direct phone numbers. No middleman.</p>
            <span class="stats">{len(map_data)} Pilots Available</span>
            
            <select id="serviceFilter" onchange="filterMap()">
                <option value="All">Show All Services</option>
                {filter_options}
            </select>

            <button class="btn btn-locate" onclick="locateUser()">📍 Find Near Me</button>
            <a href="mailto:{CONTACT_EMAIL}?subject=Add My Business" class="btn btn-add">➕ Add My Business</a>
        </div>

        <div id="map"></div>
        
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            var map = L.map('map').setView([39.8283, -98.5795], 5);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap'
            }}).addTo(map);

            var allPilots = {js_array};
            var markers = [];

            function renderMap(pilots) {{
                // Clear existing markers
                markers.forEach(m => map.removeLayer(m));
                markers = [];

                pilots.forEach(p => {{
                    var marker = L.marker([p.lat, p.lng])
                        .bindPopup(`<b>${{p.name}}</b><br><small>${{p.category}}</small><br><br><a href="${{p.url}}">View Profile</a>`);
                    marker.addTo(map);
                    markers.push(marker);
                }});
            }}

            // Initial Render
            renderMap(allPilots);

            // Filter Function
            function filterMap() {{
                var category = document.getElementById('serviceFilter').value;
                if (category === "All") {{
                    renderMap(allPilots);
                }} else {{
                    var filtered = allPilots.filter(p => p.category === category);
                    renderMap(filtered);
                }}
            }}

            // GPS Locator
            function locateUser() {{
                if (!navigator.geolocation) {{ alert("Geolocation not supported"); return; }}
                navigator.geolocation.getCurrentPosition(pos => {{
                    var lat = pos.coords.latitude;
                    var lng = pos.coords.longitude;
                    map.flyTo([lat, lng], 9);
                    L.circleMarker([lat, lng], {{color: 'blue', radius: 10}}).addTo(map).bindPopup("You are here").openPopup();
                }}, () => alert("Could not find location"));
            }}
        </script>
    </body>
    </html>
    """
    
    with open(f"{OUTPUT_DIR}/index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    
    # --- STEP 2: GENERATE SEO PROFILES ---
    print("Building SEO Profiles...")
    for _, row in df.iterrows():
        name = clean_text(row.get('Name'))
        city = clean_text(row.get('City'))
        state = clean_text(row.get('State'))
        bio = clean_text(row.get('Bio'))
        phone = clean_text(row.get('Found_Phone', 'Number Pending'))
        category = guess_category(name, bio)
        
        slug = slugify(f"{name}-{city}")
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{name} | {category} in {city}, {state}</title>
            <meta name="description" content="Hire {name} for {category} in {city}, {state}. Direct phone number: {phone}. No middleman fees.">
            
            <meta property="og:type" content="business.business">
            <meta property="og:title" content="{name} - {category}">
            <meta property="og:description" content="Call {name} directly at {phone} for drone services in {state}.">
            <meta property="og:url" content="{DOMAIN}/pilot/{slug}.html">
            
            <style>
                body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }}
                .hero {{ background: #f8f9fa; padding: 40px; text-align: center; border-radius: 10px; margin-bottom: 20px; }}
                h1 {{ color: #2c3e50; margin-bottom: 5px; }}
                .tag {{ background: #e0f7fa; color: #006064; padding: 5px 10px; border-radius: 15px; font-size: 0.9rem; display: inline-block; margin-bottom: 20px; }}
                .btn {{ background: #27ae60; color: white; padding: 15px 30px; text-decoration: none; font-size: 1.3rem; border-radius: 5px; display: inline-block; margin-top: 20px; font-weight: bold; }}
                .btn:hover {{ background: #219150; }}
                .back-link {{ text-decoration: none; color: #666; font-size: 0.9rem; }}
            </style>
        </head>
        <body>
            <a href="../index.html" class="back-link">← Back to Map</a>
            <div class="hero">
                <h1>{name}</h1>
                <p>📍 {city}, {state}</p>
                <div class="tag">{category}</div>
                <br>
                <a href="tel:{phone}" class="btn">📞 Call Now: {phone}</a>
            </div>
            
            <h2>About this Pilot</h2>
            <p>{bio if bio else "No additional information provided."}</p>
            
            <hr>
            <p style="font-size:0.8rem; color:#999; text-align:center;">
                Listing generated by {SITE_NAME}. <a href="mailto:{CONTACT_EMAIL}">Claim this profile</a>.
            </p>
        </body>
        </html>
        """
        with open(f"{OUTPUT_DIR}/pilot/{slug}.html", "w", encoding="utf-8") as f:
            f.write(html)

    print("✅ SITE UPGRADED.")
    print("Features added: Filters, Locate Button, SEO Tags, Add Me Form.")

if __name__ == "__main__":
    build_website()