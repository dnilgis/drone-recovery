import csv
import os
import re
import json
import random
from datetime import datetime

# --- CONFIGURATION ---
# UPDATED: Reads your new geocoded file directly
DB_FILE = "final_leads_geocoded.csv" 
BRAND_NAME = "The Drone Map"
DOMAIN = "https://dnilgis.github.io/drone-recovery"

# --- PREMIUM DATA OVERRIDES (Loke Drone Exclusive) ---
PREMIUM_PILOTS = {
    "loke drone": {
        "lat": 45.3164,  # Chetek, WI Center Override
        "lng": -91.6559,
        "website": "https://www.lokedrone.com",
        "bio": "Loke Drone is Chetek's premier aerial imaging provider. We specialize in precision agriculture, thermal recovery, and infrastructure inspection. FAA Part 107 certified and fully insured.",
        "services": ["Thermal Imaging", "Deer Recovery", "Ag Spraying", "Mapping"],
        "badges": ["FAA Part 107", "Fully Insured", "Verified Partner"]
    }
}

def clean_slug(text):
    return re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')

def get_jitter():
    return random.uniform(-0.025, 0.025)

def clean_coord(value):
    if not value: return None
    # Fixes "45.123; 45.124" errors
    if ";" in str(value): value = str(value).split(";")[0]
    try: return float(str(value).strip())
    except: return None

# --- 1. THE MAP (HOME) ---
index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{brand} | Find Verified Pilots</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{ --primary: #0f172a; --accent: #f97316; --glass: rgba(255, 255, 255, 0.98); }}
        body {{ margin: 0; font-family: 'Outfit', sans-serif; display: flex; flex-direction: column; height: 100vh; }}
        
        /* HEADER */
        header {{ background: white; height: 60px; display: flex; justify-content: space-between; align-items: center; padding: 0 24px; border-bottom: 2px solid #f1f5f9; z-index: 2000; }}
        .logo {{ font-weight: 800; font-size: 1.3rem; color: var(--primary); text-decoration: none; text-transform: uppercase; letter-spacing: -0.5px; }}
        .logo span {{ color: var(--accent); }}
        .nav-btn {{ background: var(--primary); color: white; padding: 10px 20px; border-radius: 8px; font-weight: 700; font-size: 0.9rem; text-decoration: none; border-bottom: 3px solid #020617; transition: 0.1s; }}
        .nav-btn:hover {{ transform: translateY(1px); border-bottom-width: 0; }}

        /* MAP AREA */
        #map {{ flex: 1; width: 100%; background: #f8fafc; z-index: 1; }}

        /* FOOTER (Fixed to bottom, High Z-Index) */
        footer {{ 
            background: white; 
            border-top: 4px solid var(--accent); /* ORANGE ACCENT */
            padding: 15px 24px; 
            display: flex; justify-content: space-between; 
            font-size: 0.8rem; color: #64748b; 
            font-weight: 600;
            z-index: 3000; /* Highest priority */
            box-shadow: 0 -4px 20px rgba(0,0,0,0.05);
        }}

        /* CONTROLS BOX */
        .controls {{ 
            position: absolute; top: 80px; right: 20px; width: 260px; 
            background: var(--glass); backdrop-filter: blur(12px); 
            padding: 20px; border-radius: 16px; 
            box-shadow: 0 10px 40px rgba(249, 115, 22, 0.15); /* Orange Glow */
            border: 1px solid white; border-top: 4px solid var(--accent);
            z-index: 1000; 
        }}
        .control-title {{ font-size: 0.7rem; font-weight: 800; letter-spacing: 0.1em; color: #64748b; text-transform: uppercase; margin-bottom: 12px; }}
        
        /* BUTTONS */
        .btn-locate {{ display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 12px 0; margin-bottom: 20px; background: white; border: 1px solid #cbd5e1; border-radius: 8px; font-weight: 700; color: #334155; cursor: pointer; transition: 0.2s; }}
        .btn-locate:hover {{ background: #fff7ed; border-color: var(--accent); color: var(--accent); }}

        /* TOGGLE */
        .toggle-row {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px; }}
        .switch {{ position: relative; display: inline-block; width: 44px; height: 24px; }}
        .switch input {{ opacity: 0; width: 0; height: 0; }}
        .slider {{ position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #cbd5e1; transition: .4s; border-radius: 34px; }}
        .slider:before {{ position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }}
        input:checked + .slider {{ background-color: var(--accent); }}
        input:checked + .slider:before {{ transform: translateX(20px); }}

        select {{ width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-family: 'Outfit', sans-serif; font-size: 0.9rem; outline: none; }}
        select:focus {{ border-color: var(--accent); }}

        /* POPUP UI */
        .leaflet-popup-content-wrapper {{ border-radius: 12px; border-top: 4px solid var(--accent); }}
        .leaflet-popup-content {{ font-family: 'Outfit', sans-serif; }}
        .badge {{ background: #ffedd5; color: #c2410c; padding: 3px 8px; border-radius: 100px; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; }}
        .btn-link {{ display: block; margin-top: 10px; text-decoration: none; font-weight: 800; font-size: 0.9rem; color: var(--accent); }}
    </style>
</head>
<body>

<header>
    <a href="index.html" class="logo">{brand}<span>.</span></a>
    <a href="join.html" class="nav-btn">List Your Business</a>
</header>

<div class="controls">
    <button class="btn-locate" onclick="locateUser()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v8M8 12h8"/></svg>
        Use My Location
    </button>

    <div class="control-title">Filter Options</div>
    <div class="toggle-row">
        <span style="font-weight:700; color:#1e293b;">Verified Only</span>
        <label class="switch">
            <input type="checkbox" id="verifiedToggle" checked onchange="updateMap()">
            <span class="slider"></span>
        </label>
    </div>

    <div class="control-title" style="margin-top:20px;">Industry</div>
    <select id="industrySelect" onchange="updateMap()">
        <option value="All">All Services</option>
        <option value="Agriculture">Agriculture</option>
        <option value="Real Estate">Real Estate</option>
        <option value="Construction">Construction</option>
        <option value="Inspection">Thermal / Inspection</option>
    </select>
</div>

<div id="map"></div>

<footer>
    <div>{count} Drone Operators Active</div>
    <div>&copy; 2026 {brand} Network</div>
</footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    var map = L.map('map', {{ zoomControl: false, preferCanvas: true }}).setView([39.8283, -98.5795], 5);
    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{ maxZoom: 19 }}).addTo(map);

    // ICONS
    var verifiedIcon = L.divIcon({{ className: 'icon-v', html: `<svg viewBox="0 0 24 24" width="40" height="40" fill="#f97316" stroke="white" stroke-width="2" style="filter:drop-shadow(0 4px 8px rgba(249,115,22,0.5));"><path d="M21 16.5c0 .38-.21.71-.53.88l-7.97 4.43c-.16.09-.33.14-.5.14s-.34-.05-.5-.14l-7.97-4.43c-.32-.17-.53-.5-.53-.88V7.5c0-.38.21-.71.53-.88l7.97-4.43c.16-.09.33-.14.5-.14s.34.05.5.14l7.97 4.43c.32.17.53.5.53.88v9z"/></svg>`, iconSize: [40, 40], iconAnchor: [20, 20], popupAnchor: [0, -10] }});
    
    // DARKER GREY PIN (#475569)
    var basicIcon = L.divIcon({{ className: 'icon-b', html: `<svg viewBox="0 0 24 24" width="14" height="14" fill="#475569" stroke="white" stroke-width="1"><circle cx="12" cy="12" r="10"/></svg>`, iconSize: [14, 14], iconAnchor: [7, 7], popupAnchor: [0, -4] }});

    var allPilots = {json_data};
    var layerGroup = L.layerGroup().addTo(map);

    function updateMap() {{
        layerGroup.clearLayers();
        var showVerified = document.getElementById('verifiedToggle').checked;
        var industry = document.getElementById('industrySelect').value;

        allPilots.forEach(p => {{
            if (showVerified && !p.verified) return;
            if (industry !== 'All' && !(p.industry || "").toLowerCase().includes(industry.toLowerCase())) return;

            var icon = p.verified ? verifiedIcon : basicIcon;
            var zIndex = p.verified ? 1000 : 1;
            
            var contact = p.phone ? `<div>📞 <a href="tel:${{p.phone}}" style="color:#0f172a;text-decoration:none;">${{p.phone}}</a></div>` : '';
            
            var content = '';
            if(p.verified) {{
                // Verified Pop-up
                content = `<span class="badge">Verified Partner</span><h3 style="margin:8px 0 4px 0;font-size:1.1rem;">${{p.name}}</h3><div style="color:#64748b;margin-bottom:8px;">${{p.city}}, ${{p.state}}</div>${{contact}}<a href="${{p.url}}" class="btn-link">View Full Profile &rarr;</a>`;
            }} else {{
                // Unverified Pop-up
                content = `<h3 style="margin:0 0 4px 0;font-size:1rem;color:#475569;">${{p.name}}</h3><div style="color:#64748b;font-size:0.9rem;">${{p.city}}, ${{p.state}}</div><div style="margin-top:5px;font-size:0.85rem;">${{contact}}</div><a href="join.html?claim=${{p.slug}}" class="btn-link" style="color:#94a3b8;font-weight:600;">Add Website & Logo +</a>`;
            }}

            L.marker([p.lat, p.lng], {{icon: icon, zIndexOffset: zIndex}}).bindPopup(content).addTo(layerGroup);
        }});
    }}

    function locateUser() {{
        map.locate({{setView: true, maxZoom: 10}});
    }}
    
    map.on('locationfound', function(e) {{
        L.marker(e.latlng).addTo(map).bindPopup("<b>You are here</b>").openPopup();
        L.circle(e.latlng, e.accuracy).addTo(map);
    }});

    updateMap();
</script>
</body>
</html>
"""

# --- 2. PREMIUM PROFILE TEMPLATE ---
profile_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} | Verified Drone Partner</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; font-family: 'Outfit', sans-serif; background: #f8fafc; color: #0f172a; }}
        
        .hero {{ background: #0f172a; color: white; padding: 60px 20px; text-align: center; border-bottom: 4px solid #f97316; }}
        .hero h1 {{ margin: 0; font-size: 2.5rem; letter-spacing: -1px; }}
        .hero p {{ color: #94a3b8; font-size: 1.2rem; margin-top: 10px; }}
        
        .container {{ max-width: 800px; margin: -40px auto 40px; padding: 0 20px; }}
        .card {{ background: white; border-radius: 20px; box-shadow: 0 20px 40px -10px rgba(0,0,0,0.1); overflow: hidden; }}
        
        .trust-bar {{ background: #f1f5f9; padding: 15px; display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; border-bottom: 1px solid #e2e8f0; }}
        .trust-badge {{ display: flex; align-items: center; gap: 6px; font-weight: 700; font-size: 0.85rem; color: #475569; }}
        .trust-badge svg {{ width: 16px; height: 16px; color: #10b981; }}

        .content {{ padding: 40px; }}
        .bio {{ font-size: 1.1rem; line-height: 1.6; color: #334155; margin-bottom: 30px; }}
        .section-title {{ font-size: 0.9rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; margin-bottom: 15px; }}
        .tags {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 30px; }}
        .tag {{ background: #fff7ed; color: #c2410c; padding: 8px 16px; border-radius: 8px; font-weight: 700; font-size: 0.9rem; border: 1px solid #ffedd5; }}

        .action-bar {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px; }}
        .btn {{ display: flex; align-items: center; justify-content: center; gap: 10px; padding: 16px; border-radius: 12px; font-weight: 700; text-decoration: none; font-size: 1.1rem; transition: 0.2s; }}
        .btn-primary {{ background: #f97316; color: white; box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3); }}
        .btn-primary:hover {{ transform: translateY(-2px); }}
        .btn-secondary {{ background: white; border: 2px solid #e2e8f0; color: #0f172a; }}
        
        .back-link {{ display: block; text-align: center; margin-top: 30px; color: #94a3b8; text-decoration: none; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>{name}</h1>
        <p>{city}, {state} • Verified Partner</p>
    </div>
    <div class="container">
        <div class="card">
            <div class="trust-bar">{badges_html}</div>
            <div class="content">
                <div class="section-title">About</div>
                <div class="bio">{bio}</div>
                <div class="section-title">Services</div>
                <div class="tags">{services_html}</div>
                <div class="section-title">Fleet</div>
                <div style="font-size: 1.1rem; color: #334155; margin-bottom: 30px;">{equipment}</div>
                <div class="action-bar">
                    <a href="{website}" target="_blank" class="btn btn-secondary">🌐 Website</a>
                    <a href="tel:{phone}" class="btn btn-primary">📞 Call Now</a>
                </div>
            </div>
        </div>
        <a href="../index.html" class="back-link">&larr; Back to Drone Map</a>
    </div>
</body>
</html>
"""

# --- 3. SALES PAGE ---
join_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Get Verified | {brand}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Outfit', sans-serif; background: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
        .card {{ background: white; padding: 48px; border-radius: 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.05); max-width: 440px; text-align: center; border-top: 6px solid #f97316; }}
        h1 {{ margin-top: 0; font-size: 2rem; color: #0f172a; letter-spacing: -1px; }}
        .price {{ font-size: 3.5rem; font-weight: 800; color: #f97316; margin: 10px 0; }}
        .features {{ text-align: left; margin: 32px 0; font-size: 1.1rem; color: #475569; line-height: 2; }}
        .btn {{ display: block; background: #0f172a; color: white; padding: 18px; border-radius: 12px; font-weight: 700; text-decoration: none; font-size: 1.1rem; transition: 0.2s; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Verified Partner</h1>
        <p style="color:#64748b; font-size:1.1rem;">Dominate your local market.</p>
        <div class="price">$49<span style="font-size:1rem; font-weight:600; color:#94a3b8;">/yr</span></div>
        <ul class="features">
            <li>✅ <b>SEO Backlink:</b> Link to your Website</li>
            <li>✅ <b>Trust:</b> Verified Orange Badge</li>
            <li>✅ <b>Conversion:</b> Add Logo, Bio & Tags</li>
            <li>✅ <b>Priority:</b> Rank #1 in your City</li>
        </ul>
        <a href="mailto:sales@dronemap.com" class="btn">Claim Your Listing</a>
        <a href="index.html" style="display:block; margin-top:20px; color:#94a3b8; text-decoration:none; font-weight:600;">No thanks, return to map</a>
    </div>
</body>
</html>
"""

def run_build():
    if not os.path.exists("pilot"): os.makedirs("pilot")
    map_data = []

    if not os.path.exists(DB_FILE):
        print(f"ERROR: {DB_FILE} not found!")
        return

    with open(DB_FILE, newline='', encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            name = row.get('Name', 'Drone Operator').strip()
            city = row.get('City', '').strip()
            state = row.get('State', '').strip()
            phone = row.get('Phone', '').strip()
            
            lat = clean_coord(row.get('Latitude'))
            lng = clean_coord(row.get('Longitude'))

            is_verified = False
            premium_info = {}
            
            for p_name, p_data in PREMIUM_PILOTS.items():
                if p_name in name.lower():
                    is_verified = True
                    premium_info = p_data
                    lat = p_data['lat']
                    lng = p_data['lng']
                    break
            
            if lat and lng:
                slug = clean_slug(f"{name}-{city}-{state}")
                pilot_obj = {
                    "name": name,
                    "city": city,
                    "state": state,
                    "phone": phone,
                    "lat": float(lat) + get_jitter(),
                    "lng": float(lng) + get_jitter(),
                    "verified": is_verified,
                    "slug": slug,
                    "industry": row.get('Industry', 'General'),
                    "url": "#"
                }

                if is_verified:
                    pilot_obj["url"] = f"pilot/{slug}.html"
                    badges_html = "".join([f'<div class="trust-badge"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>{b}</div>' for b in premium_info.get('badges', [])])
                    services_html = "".join([f'<span class="tag">{s}</span>' for s in premium_info.get('services', [])])
                    
                    with open(f"pilot/{slug}.html", "w", encoding="utf-8") as p:
                        p.write(profile_template.format(
                            brand=BRAND_NAME,
                            name=name, city=city, state=state,
                            phone=phone or "No Phone",
                            website=premium_info.get('website', '#'),
                            bio=premium_info.get('bio', 'Professional Drone Operator.'),
                            badges_html=badges_html,
                            services_html=services_html,
                            equipment=row.get('Equipment_Details', 'Standard Fleet')
                        ))
                
                map_data.append(pilot_obj)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html.format(brand=BRAND_NAME, count=len(map_data), json_data=json.dumps(map_data)))
        
    with open("join.html", "w", encoding="utf-8") as f:
        f.write(join_html.format(brand=BRAND_NAME))

    print(f"SUCCESS: Mapped {len(map_data)} Pilots. Verified Toggle Defaults to ON.")

if __name__ == "__main__":
    run_build()