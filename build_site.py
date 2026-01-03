import csv
import os
import re
import json
import random
import shutil
import time

# --- CONFIGURATION ---
DB_FILE = "final_leads_geocoded.csv"
BRAND_NAME = "The Drone Map"
DOMAIN = "https://dnilgis.github.io/drone-recovery"

# --- PREMIUM DATA (Loke Drone) ---
PREMIUM_PILOTS = {
    "loke drone": {
        "lat": 45.3164, "lng": -91.6559,
        "website": "https://www.lokedrone.com",
        "bio": "Loke Drone is Chetek's premier aerial imaging provider. Specializing in thermal recovery and precision ag.",
        "badges": ["FAA Part 107", "Verified Partner", "Thermal Expert"],
        "services": ["Thermal", "Deer Recovery", "Agriculture"]
    }
}

def clean_slug(text): 
    slug = re.sub(r'[^a-z0-9]+', '-', str(text).lower()).strip('-')
    return slug[:50]

def get_jitter(): return random.uniform(-0.005, 0.005)

def clean_coord(value):
    if not value: return None
    if ";" in str(value): value = str(value).split(";")[0]
    try: return float(str(value).strip())
    except: return None

# --- ROBUST DIRECTORY CLEANER ---
def safe_prepare_dir(path):
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except:
            pass # Silently ignore permission errors
    if not os.path.exists(path):
        os.makedirs(path)

# --- TEMPLATES ---
index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <title>{brand} | Find Verified Pilots</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet-geosearch@3.0.0/dist/geosearch.css" />
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{ --primary: #0f172a; --accent: #f97316; --glass: rgba(255, 255, 255, 0.98); }}
        body {{ margin: 0; font-family: 'Outfit', sans-serif; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }}
        header {{ background: white; height: 60px; display: flex; justify-content: space-between; align-items: center; padding: 0 20px; border-bottom: 2px solid #f1f5f9; z-index: 2000; }}
        .logo {{ font-weight: 800; font-size: 1.2rem; color: var(--primary); text-decoration: none; text-transform: uppercase; }}
        .logo span {{ color: var(--accent); }}
        .nav-link {{ font-weight: 700; color: #64748b; text-decoration: none; font-size: 0.9rem; margin-right: 15px; display: none; }}
        .nav-btn {{ background: var(--primary); color: white; padding: 8px 16px; border-radius: 8px; font-weight: 700; text-decoration: none; font-size: 0.9rem; }}
        @media(min-width:600px) {{ .nav-link {{ display: inline-block; }} }}
        #map {{ flex: 1; width: 100%; background: #f8fafc; z-index: 1; }}
        .controls {{ position: absolute; top: 80px; right: 20px; width: 260px; background: var(--glass); backdrop-filter: blur(12px); padding: 20px; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); border-top: 4px solid var(--accent); z-index: 1000; transition: transform 0.3s; }}
        @media(max-width: 600px) {{ .controls {{ top: auto; bottom: 80px; right: 10px; left: 10px; width: auto; transform: translateY(150%); }} .controls.active {{ transform: translateY(0); }} }}
        .control-title {{ font-size: 0.7rem; font-weight: 800; text-transform: uppercase; color: #64748b; margin-bottom: 10px; letter-spacing: 1px; }}
        .toggle-row {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }}
        .switch {{ position: relative; display: inline-block; width: 40px; height: 22px; }}
        .switch input {{ opacity: 0; width: 0; height: 0; }}
        .slider {{ position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #cbd5e1; transition: .4s; border-radius: 34px; }}
        .slider:before {{ position: absolute; content: ""; height: 16px; width: 16px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; }}
        input:checked + .slider {{ background-color: var(--accent); }}
        input:checked + .slider:before {{ transform: translateX(18px); }}
        select {{ width: 100%; padding: 10px; border: 1px solid #e2e8f0; border-radius: 8px; font-family: 'Outfit', sans-serif; outline: none; }}
        .filter-fab {{ position: absolute; bottom: 90px; right: 20px; width: 50px; height: 50px; background: var(--primary); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; z-index: 999; box-shadow: 0 4px 15px rgba(0,0,0,0.2); cursor: pointer; display: none; }}
        @media(max-width: 600px) {{ .filter-fab {{ display: flex; }} }}
        footer {{ background: white; border-top: 1px solid #e2e8f0; padding: 10px 20px; font-size: 0.8rem; color: #64748b; font-weight: 600; display: flex; justify-content: space-between; z-index: 2000; }}
        .leaflet-popup-content-wrapper {{ border-radius: 12px; padding: 0; }}
        .leaflet-popup-content {{ margin: 0; width: 280px !important; }}
        .popup-header {{ background: #0f172a; color: white; padding: 15px; border-radius: 12px 12px 0 0; position: relative; }}
        .popup-header h3 {{ margin: 0; font-size: 1rem; }}
        .popup-body {{ padding: 15px; }}
        .badge {{ background: #f97316; color: white; font-size: 0.6rem; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; font-weight: 800; position: absolute; top: 10px; right: 10px; }}
        .btn-claim {{ display: block; background: #f1f5f9; color: #0f172a; text-align: center; padding: 8px; border-radius: 6px; text-decoration: none; font-weight: 700; margin-top: 10px; font-size: 0.9rem; }}
        .marker-cluster-small {{ background-color: rgba(249, 115, 22, 0.6); }}
        .marker-cluster-small div {{ background-color: rgba(249, 115, 22, 0.8); color: white; font-weight: 800; }}
        .marker-cluster-medium {{ background-color: rgba(15, 23, 42, 0.6); }}
        .marker-cluster-medium div {{ background-color: rgba(15, 23, 42, 0.8); color: white; font-weight: 800; }}
    </style>
</head>
<body>
<header>
    <a href="index.html" class="logo">{brand}<span>.</span></a>
    <div><a href="directory/index.html" class="nav-link">Directory</a><a href="join.html" class="nav-btn">Add Business</a></div>
</header>
<div id="map"></div>
<div class="filter-fab" onclick="document.querySelector('.controls').classList.toggle('active')"><svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/></svg></div>
<div class="controls">
    <div class="control-title">Map Filters</div>
    <div class="toggle-row">
        <span>Verified Only</span>
        <label class="switch"><input type="checkbox" id="verifiedToggle" onchange="updateMap()"><span class="slider"></span></label>
    </div>
    <div class="control-title" style="margin-top:15px">Industry</div>
    <select id="industrySelect" onchange="updateMap()">
        <option value="All">All Industries</option>
        <option value="Agriculture">Agriculture</option>
        <option value="Thermal">Thermal Inspection</option>
        <option value="Deer Recovery">Deer Recovery</option>
        <option value="Government">Public Safety</option>
        <option value="Defense">Defense</option>
        <option value="Real Estate">Real Estate</option>
    </select>
</div>
<footer><a href="directory/index.html" style="color:#64748b; text-decoration:none;">Browse Directory</a><span>&copy; 2026 {brand} (v6.0)</span></footer>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js"></script>
<script src="https://unpkg.com/leaflet-geosearch@3.0.0/dist/bundle.min.js"></script>
<script>
    var map = L.map('map', {{ zoomControl: false }}).setView([39.8283, -98.5795], 5);
    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{ maxZoom: 19 }}).addTo(map);
    const searchControl = new GeoSearch.GeoSearchControl({{ provider: new GeoSearch.OpenStreetMapProvider(), style: 'bar', showMarker: false, autoClose: true }});
    map.addControl(searchControl);
    var markers = L.markerClusterGroup({{ showCoverageOnHover: false, maxClusterRadius: 50 }});
    var allPilots = {json_data};
    
    var verifiedIcon = L.divIcon({{ className: 'v-icon', html: '<div style="background:#f97316;width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 2px 5px rgba(0,0,0,0.3);"></div>', iconSize: [16, 16] }});
    var basicIcon = L.divIcon({{ className: 'b-icon', html: '<div style="background:#64748b;width:10px;height:10px;border-radius:50%;border:2px solid white;"></div>', iconSize: [14, 14] }});

    function updateMap() {{
        markers.clearLayers();
        var showVerified = document.getElementById('verifiedToggle').checked;
        var industry = document.getElementById('industrySelect').value;
        allPilots.forEach(p => {{
            if (showVerified && !p.verified) return;
            if (industry !== 'All') {{
                var p_tags = (p.industry || "").toLowerCase();
                var search = industry.toLowerCase();
                if (search === 'thermal' && !p_tags.includes('thermal') && !p_tags.includes('inspection')) return;
                else if (search !== 'thermal' && !p_tags.includes(search)) return;
            }}
            var icon = p.verified ? verifiedIcon : basicIcon;
            var content = '';
            if(p.verified) {{
                content = `<div class="popup-header"><h3>${{p.name}}</h3><div class="badge">VERIFIED</div></div><div class="popup-body"><div style="color:#64748b; font-size:0.9rem; margin-bottom:10px;">${{p.city}}, ${{p.state}}</div><a href="${{p.url}}" class="btn-claim" style="background:#f97316; color:white;">View Profile</a></div>`;
            }} else {{
                var claimLink = `join.html?claim=${{p.slug}}&name=${{encodeURIComponent(p.name)}}&city=${{encodeURIComponent(p.city)}}`;
                var websiteBtn = p.website ? `<a href="${{p.website}}" target="_blank" style="display:block; text-align:center; color:#2563eb; font-weight:700; margin-bottom:8px; font-size:0.8rem;">Visit Website &rarr;</a>` : '';
                content = `<div class="popup-header" style="background:#f1f5f9; color:#0f172a;"><h3>${{p.name}}</h3></div><div class="popup-body"><div style="color:#64748b; font-size:0.9rem; margin-bottom:10px;">${{p.city}}, ${{p.state}}</div>${{websiteBtn}}<a href="${{claimLink}}" class="btn-claim">Is this you? Claim it.</a></div>`;
            }}
            var m = L.marker([p.lat, p.lng], {{icon: icon}}).bindPopup(content);
            markers.addLayer(m);
        }});
        map.addLayer(markers);
    }}

    // FORCE TOGGLE OFF ON LOAD (Fixes "Sticky Checkbox" Issue)
    window.onload = function() {{
        document.getElementById('verifiedToggle').checked = false;
        updateMap();
    }};
</script>
</body>
</html>
"""

directory_template = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{title} | {brand}</title><link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet"><style>body{{font-family:'Outfit',sans-serif;background:#f8fafc;color:#0f172a;margin:0;padding:40px;max-width:800px;margin:0 auto}}h1{{font-size:2rem;border-bottom:4px solid #f97316;padding-bottom:10px}}.breadcrumb{{color:#64748b;font-weight:600;margin-bottom:20px}}.breadcrumb a{{text-decoration:none;color:#64748b}}.list{{list-style:none;padding:0}}.list li{{background:white;padding:20px;border-radius:12px;margin-bottom:15px;box-shadow:0 4px 10px rgba(0,0,0,0.05);display:flex;justify-content:space-between;align-items:center}}.list a{{text-decoration:none;color:#0f172a;font-weight:700;font-size:1.1rem}}</style></head><body><div class="breadcrumb"><a href="{root_path}index.html">Home</a> / {breadcrumb}</div><h1>{header}</h1><ul class="list">{list_items}</ul></body></html>"""

join_html = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Claim Listing</title><link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet"><style>body{{font-family:'Outfit',sans-serif;background:#f8fafc;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}}.card{{background:white;padding:48px;border-radius:24px;box-shadow:0 10px 40px rgba(0,0,0,0.05);max-width:440px;text-align:center;border-top:6px solid #f97316}}.btn{{display:block;background:#0f172a;color:white;padding:18px;border-radius:12px;font-weight:700;text-decoration:none;font-size:1.1rem;cursor:pointer}}</style></head><body><div class="card"><h1 id="header">Verified Partner</h1><p id="sub" style="color:#64748b;font-size:1.1rem">Dominate your local market.</p><div style="font-size:3.5rem;font-weight:800;color:#f97316;margin:10px 0">$49<span style="font-size:1rem;font-weight:600;color:#94a3b8">/yr</span></div><ul style="text-align:left;color:#475569;line-height:2;margin:30px 0"><li>✅ <b>Priority Rank:</b> Be #1 in <span id="city_name">your area</span></li><li>✅ <b>SEO Power:</b> Backlink to your site</li><li>✅ <b>Trust:</b> Verified Orange Badge</li></ul><a href="#" class="btn" id="claimBtn">Proceed to Checkout</a><a href="index.html" style="display:block;margin-top:20px;color:#94a3b8;text-decoration:none;font-weight:600">Return to Map</a></div><script>const params=new URLSearchParams(window.location.search);const name=params.get('name');const city=params.get('city');if(name){{document.getElementById('header').innerText="Claim "+name;document.getElementById('sub').innerText="Unlock full profile features.";document.getElementById('claimBtn').href=`mailto:sales@dronemap.com?subject=Claiming ${{name}}&body=I want to claim the listing for ${{name}} in ${{city}}.`;}}if(city){{document.getElementById('city_name').innerText=city;}}</script></body></html>"""

profile_template = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{name}</title><link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet"><style>body{{margin:0;font-family:'Outfit',sans-serif;background:#f8fafc;color:#0f172a}}.hero{{background:#0f172a;color:white;padding:60px 20px;text-align:center;border-bottom:4px solid #f97316}}.container{{max-width:800px;margin:-40px auto 40px;padding:0 20px}}.card{{background:white;border-radius:20px;box-shadow:0 20px 40px -10px rgba(0,0,0,0.1);overflow:hidden}}.trust-bar{{background:#f1f5f9;padding:15px;display:flex;gap:15px;justify-content:center;flex-wrap:wrap;border-bottom:1px solid #e2e8f0}}.trust-badge{{display:flex;align-items:center;gap:6px;font-weight:700;font-size:0.85rem;color:#475569}}.content{{padding:40px}}.section-title{{font-size:0.9rem;font-weight:800;text-transform:uppercase;color:#94a3b8;margin-bottom:15px}}.tags{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:30px}}.tag{{background:#fff7ed;color:#c2410c;padding:8px 16px;border-radius:8px;font-weight:700;font-size:0.9rem;border:1px solid #ffedd5}}.btn{{display:flex;align-items:center;justify-content:center;padding:16px;border-radius:12px;font-weight:700;text-decoration:none;font-size:1.1rem;transition:0.2s}}.btn-primary{{background:#f97316;color:white}}.btn-secondary{{background:white;border:2px solid #e2e8f0;color:#0f172a}}</style></head><body><div class="hero"><h1>{name}</h1><p>{city}, {state} • Verified Partner</p></div><div class="container"><div class="card"><div class="trust-bar">{badges_html}</div><div class="content"><div class="section-title">About</div><div style="font-size:1.1rem;line-height:1.6;margin-bottom:30px">{bio}</div><div class="section-title">Services</div><div class="tags">{services_html}</div><div class="section-title">Fleet</div><div style="margin-bottom:30px">{equipment}</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:15px"><a href="{website}" class="btn btn-secondary">Website</a><a href="tel:{phone}" class="btn btn-primary">Call Now</a></div></div></div><a href="../index.html" style="display:block;text-align:center;margin-top:30px;color:#94a3b8;text-decoration:none;font-weight:600">&larr; Back to Map</a></div></body></html>"""

def run_build():
    if not os.path.exists(DB_FILE):
        print(f"ERROR: {DB_FILE} not found!")
        return

    safe_prepare_dir("directory")
    safe_prepare_dir("pilot")

    map_data = []
    seo_tree = {} 

    with open(DB_FILE, newline='', encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row.get('Name', '').strip()
            city = row.get('City', '').strip().title()
            state = row.get('State', '').strip().upper()
            lat = clean_coord(row.get('Latitude'))
            lng = clean_coord(row.get('Longitude'))
            
            if len(state) > 2 or ";" in state: state = "OTHER"

            is_verified = False
            premium_info = {}
            for p_name, p_data in PREMIUM_PILOTS.items():
                if p_name in name.lower():
                    is_verified = True
                    premium_info = p_data
                    lat, lng = p_data['lat'], p_data['lng']
                    break
            
            if lat and lng:
                slug = clean_slug(f"{name}-{city}-{state}")
                pilot_obj = {
                    "name": name, "city": city, "state": state,
                    "lat": float(lat) + get_jitter(), "lng": float(lng) + get_jitter(),
                    "verified": is_verified, "slug": slug,
                    "industry": row.get('Industry', ''),
                    "website": row.get('Enriched_URL') if row.get('Enriched_URL') else row.get('Website', ''),
                    "url": "#"
                }

                if state != "OTHER":
                    if state not in seo_tree: seo_tree[state] = {}
                    if city not in seo_tree[state]: seo_tree[state][city] = []
                    seo_tree[state][city].append(pilot_obj)

                if is_verified:
                    pilot_obj["url"] = f"pilot/{slug}.html"
                    badges_html = "".join([f'<div class="trust-badge"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>{b}</div>' for b in premium_info.get('badges', [])])
                    services_html = "".join([f'<span class="tag">{s}</span>' for s in premium_info.get('services', [])])
                    with open(f"pilot/{slug}.html", "w", encoding="utf-8") as p:
                        p.write(profile_template.format(
                            name=name, city=city, state=state, phone=row.get('Phone', ''),
                            website=premium_info.get('website','#'), bio=premium_info.get('bio',''),
                            badges_html=badges_html, services_html=services_html,
                            equipment=row.get('Equipment_Details', '')
                        ))
                map_data.append(pilot_obj)

    # DIRECTORY GENERATION
    states_list_html = ""
    for state in sorted(seo_tree.keys()):
        cities = seo_tree[state]
        cities_list_html = ""
        for city in sorted(cities.keys()):
            count = len(cities[city])
            city_slug = clean_slug(city)
            pilots_in_city = cities[city]
            pilot_list_html = ""
            for p in pilots_in_city:
                link = p['url'] if p['verified'] else f"../../join.html?claim={p['slug']}&name={p['name']}&city={city}"
                pilot_list_html += f"<li><span>{p['name']}</span> <a href='{link}' style='font-size:0.9rem; color:#f97316;'>View Profile</a></li>"
            
            safe_prepare_dir(f"directory/{state}")
            with open(f"directory/{state}/{city_slug}.html", "w", encoding="utf-8") as cp:
                cp.write(directory_template.format(
                    title=f"Drone Pilots in {city}, {state}", brand=BRAND_NAME, root_path="../../",
                    breadcrumb=f"<a href='../index.html'>States</a> / <a href='../{state}.html'>{state}</a> / {city}",
                    header=f"{count} Drone Pilots in {city}, {state}", list_items=pilot_list_html
                ))
            cities_list_html += f"<li><span>{city}</span> <a href='{state}/{city_slug}.html'>{count} Pilots</a></li>"

        with open(f"directory/{state}.html", "w", encoding="utf-8") as sp:
            sp.write(directory_template.format(
                title=f"Drone Pilots in {state}", brand=BRAND_NAME, root_path="../",
                breadcrumb=f"<a href='index.html'>States</a> / {state}", header=f"Cities in {state}", list_items=cities_list_html
            ))
        states_list_html += f"<li><span>{state}</span> <a href='{state}.html'>View Cities</a></li>"

    with open("directory/index.html", "w", encoding="utf-8") as dp:
        dp.write(directory_template.format(
            title="Pilot Directory", brand=BRAND_NAME, root_path="../",
            breadcrumb="States", header="Browse Pilots by State", list_items=states_list_html
        ))

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html.format(brand=BRAND_NAME, count=len(map_data), json_data=json.dumps(map_data)))
    with open("join.html", "w", encoding="utf-8") as f:
        f.write(join_html)

    print(f"SUCCESS: V6 Launch Ready. Toggle Default: OFF (Show All).")

if __name__ == "__main__":
    run_build()