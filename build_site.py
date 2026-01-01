import pandas as pd
import os
import re
import json

# --- CONFIGURATION ---
SITE_NAME = "National Drone Directory"
CONTACT_EMAIL = "your-email@example.com" # <--- UPDATE THIS
INPUT_FILE = "drone_pilots_WITH_PHONES_FINAL.csv"
OUTPUT_DIR = "deploy_me"

def clean_text(text):
    if pd.isna(text): return ""
    return str(text).strip()

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')

# --- LOGIC UPDATE: FORCE DEER RECOVERY ---
def get_services(row):
    text = (str(row.get('Name', '')) + " " + str(row.get('Bio', '')) + " " + str(row.get('City', ''))).lower()
    
    # 1. FORCE DEER RECOVERY FOR EVERYONE (As requested)
    services = ["🦌 Deer Recovery"]
    
    # 2. Add other tags if keywords exist
    if any(x in text for x in ['ag', 'farm', 'crop', 'seed', 'spray', 'field', 'harvest', 'survey']):
        services.append("🌾 Agriculture")
    if any(x in text for x in ['photo', 'video', 'cinema', 'estate', 'survey', 'map', 'inspection', 'media']):
        services.append("📸 Photography")
    if any(x in text for x in ['thermal', 'heat', 'sar', 'search', 'rescue']):
        services.append("🔥 Thermal Imaging")
    if any(x in text for x in ['real estate', 'realtor', 'house']):
        services.append("🏠 Real Estate")
        
    return list(set(services))

def run_build():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: '{INPUT_FILE}' not found.")
        return

    print("Reading database...")
    df = pd.read_csv(INPUT_FILE)
    
    print("Building Website...")
    os.makedirs(f"{OUTPUT_DIR}/pilot", exist_ok=True)
    
    map_data = []
    
    # 1. BUILD MAP DATA
    for _, row in df.iterrows():
        try:
            coords = str(row.get('Coordinates', '0,0')).split(',')
            if len(coords) == 2:
                lat, lng = coords[0].strip(), coords[1].strip()
                name = clean_text(row.get('Name'))
                city = clean_text(row.get('City'))
                service_list = get_services(row)
                slug = slugify(f"{name}-{city}")
                
                # Clean tag name for javascript filtering
                raw_services = [s.split(' ')[1] if ' ' in s else s for s in service_list]

                pilot_info = {
                    "name": name,
                    "phone": clean_text(row.get('Found_Phone', 'Click for #')),
                    "lat": lat,
                    "lng": lng,
                    "services": raw_services, 
                    "display_services": service_list,
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
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
        <title>{SITE_NAME}</title>
        
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <style>
            body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
            #map {{ height: 100vh; width: 100%; z-index: 1; }}
            
            .info-box {{
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                position: absolute;
                top: 20px;
                right: 20px;
                z-index: 1000;
                width: 320px;
                max-width: 90%;
            }}
            
            h1 {{ margin: 0 0 5px; font-size: 1.4rem; color: #111; }}
            p {{ font-size: 0.9rem; color: #666; margin-bottom: 15px; }}
            
            select {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; margin-bottom: 10px; background: #f9f9f9; }}
            
            .btn {{ display: block; width: 100%; padding: 12px 0; text-align: center; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 8px; cursor: pointer; border: none; font-size:16px; }}
            .btn-locate {{ background: #007aff; color: white; }}
            .btn-add {{ background: #34c759; color: white; }}
            
            .badge {{ display: inline-block; background: #eee; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; margin-right: 4px; color: #555; border: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <div class="info-box">
            <h1>{SITE_NAME}</h1>
            <p><strong>{len(map_data)}</strong> Pilots Available. No fees.</p>
            
            <select id="serviceFilter" onchange="filterMap()">
                <option value="All">Show All Services</option>
                <option value="Deer">🦌 Deer Recovery</option>
                <option value="Agriculture">🌾 Agriculture</option>
                <option value="Photography">📸 Photography</option>
                <option value="Thermal">🔥 Thermal Imaging</option>
            </select>

            <button class="btn btn-locate" onclick="locateUser()">📍 Find Near Me</button>
            <a href="add-pilot.html" class="btn btn-add">➕ Add Me to Map</a>
        </div>

        <div id="map"></div>
        
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            var map = L.map('map').setView([39.8283, -98.5795], 5);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ attribution: '© OpenStreetMap' }}).addTo(map);

            var allPilots = {js_array};
            var markers = [];
            
            // CUSTOM SVG DRONE ICON (Created by code, no image file needed)
            var droneIcon = L.divIcon({{
                className: 'custom-drone',
                html: `<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="background:white; border-radius:50%; border:2px solid #333; padding:2px;">
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="M12 9V5"></path><path d="M12 15v4"></path>
                        <path d="M9 12H5"></path><path d="M15 12h4"></path>
                        <circle cx="12" cy="3" r="1"></circle><circle cx="12" cy="21" r="1"></circle>
                        <circle cx="3" cy="12" r="1"></circle><circle cx="21" cy="12" r="1"></circle>
                       </svg>`,
                iconSize: [34, 34],
                iconAnchor: [17, 17],
                popupAnchor: [0, -20]
            }});

            function renderMap(pilots) {{
                markers.forEach(m => map.removeLayer(m));
                markers = [];
                pilots.forEach(p => {{
                    var servicesHtml = p.display_services.map(s => `<span class='badge'>${{s}}</span>`).join("");
                    
                    var marker = L.marker([p.lat, p.lng], {{icon: droneIcon}})
                        .bindPopup(`<b>${{p.name}}</b><br>${{servicesHtml}}<br><br><a href="${{p.url}}">View Profile</a>`);
                    marker.addTo(map);
                    markers.push(marker);
                }});
            }}

            renderMap(allPilots);

            function filterMap() {{
                var cat = document.getElementById('serviceFilter').value;
                if(cat === "All") {{ renderMap(allPilots); return; }}
                
                // Broad match filter
                var filtered = allPilots.filter(p => p.services.some(s => s.includes(cat)));
                renderMap(filtered);
            }}

            function locateUser() {{
                if (!navigator.geolocation) {{ alert("Geolocation not supported"); return; }}
                navigator.geolocation.getCurrentPosition(pos => {{
                    var lat = pos.coords.latitude;
                    var lng = pos.coords.longitude;
                    map.flyTo([lat, lng], 10);
                    L.circleMarker([lat, lng], {{color: 'blue', radius: 15}}).addTo(map).bindPopup("You").openPopup();
                }});
            }}
        </script>
    </body>
    </html>
    """
    
    with open(f"{OUTPUT_DIR}/index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    
    # 2. GENERATE "ADD PILOT" PAGE
    add_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Your Business</title>
        <style>
            body {{ font-family: sans-serif; padding: 40px; text-align: center; background: #f4f4f9; color: #333; }}
            .card {{ background: white; max-width: 500px; margin: 0 auto; padding: 40px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            .email {{ background: #e8f5e9; padding: 15px; font-size: 1.2rem; font-weight: bold; color: #2e7d32; border-radius: 5px; display: inline-block; margin: 20px 0; border: 1px solid #c8e6c9; }}
            .btn {{ display: inline-block; background: #34c759; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 1.1rem; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>➕ Get Listed on the Map</h1>
            <p>We are building the largest directory of verified drone pilots.</p>
            <p>To add your business, please email us with your <strong>Name</strong>, <strong>City</strong>, and <strong>Phone Number</strong>.</p>
            
            <div class="email">{CONTACT_EMAIL}</div>
            <br>
            <a href="mailto:{CONTACT_EMAIL}?subject=Add My Drone Business" class="btn">Click to Email Us</a>
            <br><br><br>
            <a href="index.html" style="color:#666; text-decoration:none;">← Back to Map</a>
        </div>
    </body>
    </html>
    """
    with open(f"{OUTPUT_DIR}/add-pilot.html", "w", encoding="utf-8") as f:
        f.write(add_html)

    # 3. GENERATE PROFILES
    print("Generating Profiles...")
    for _, row in df.iterrows():
        name = clean_text(row.get('Name'))
        city = clean_text(row.get('City'))
        state = clean_text(row.get('State'))
        phone = clean_text(row.get('Found_Phone', 'Number Pending'))
        bio = clean_text(row.get('Bio'))
        slug = slugify(f"{name}-{city}")
        service_tags = "".join([f"<span class='tag'>{s}</span>" for s in get_services(row)])
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{name} | Drone Pilot</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f4f4f9; color: #333; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
                .back-link {{ text-decoration: none; color: #666; font-size: 0.9rem; display: block; margin-bottom: 20px; }}
                h1 {{ margin: 0 0 5px; color: #111; }}
                .location {{ color: #666; font-size: 1.1rem; margin-bottom: 20px; display: block; }}
                .tags {{ margin-bottom: 25px; }}
                .tag {{ display: inline-block; background: #eef2f5; padding: 5px 12px; border-radius: 20px; font-size: 0.85rem; color: #444; margin-right: 5px; margin-bottom: 5px; border: 1px solid #e1e4e8; }}
                .cta-box {{ background: #f8fff9; border: 2px solid #34c759; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 30px; }}
                .phone-btn {{ display: inline-block; background: #34c759; color: white; text-decoration: none; padding: 12px 25px; border-radius: 6px; font-weight: bold; font-size: 1.2rem; }}
                .bio {{ line-height: 1.6; color: #555; margin-bottom: 40px; border-top: 1px solid #eee; padding-top: 20px; }}
                .claim-box {{ background: #fff8e1; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #ffe082; font-size: 0.9rem; }}
                .claim-link {{ color: #f57f17; font-weight: bold; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="../index.html" class="back-link">← Back to Map</a>
                <h1>{name}</h1>
                <span class="location">📍 {city}, {state}</span>
                <div class="tags">{service_tags}</div>
                <div class="cta-box">
                    <p style="margin-top:0; color:#28a745; font-weight:bold;">Direct Phone Number</p>
                    <a href="tel:{phone}" class="phone-btn">📞 {phone}</a>
                </div>
                <div class="bio">
                    <strong>About this Pilot:</strong><br>
                    {bio if bio and str(bio) != 'nan' else "Licensed drone pilot available for services in the " + city + " area."}
                </div>
                <div class="claim-box">
                    Is this your business? <br>
                    <a href="mailto:{CONTACT_EMAIL}?subject=Claim Profile: {name}" class="claim-link">Claim & Upgrade This Profile 🚀</a>
                </div>
            </div>
        </body>
        </html>
        """
        with open(f"{OUTPUT_DIR}/pilot/{slug}.html", "w", encoding="utf-8") as f:
            f.write(html)

    print("✅ SITE BUILD COMPLETE.")

if __name__ == "__main__":
    run_build()