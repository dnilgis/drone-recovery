import csv
import os
import shutil
import re
import json
import random
from datetime import datetime

DB_FILE = "drone_pilots_WITH_PHONES_FINAL" 
if not os.path.exists(DB_FILE) and os.path.exists(DB_FILE + ".csv"):
    DB_FILE = DB_FILE + ".csv"

BRAND_NAME = "United Drone Operations"
TAGLINE = "National Infrastructure for Thermal & Agricultural Deployment"
DOMAIN = "https://uniteddroneops.com" 
CURRENT_DATE = datetime.now().strftime("%B %Y")

def clean_slug(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def get_jitter():
    return random.uniform(-0.04, 0.04)

index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{brand} | {tagline}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <style>
        :root {{ --bg: #020617; --panel: #0f172a; --accent: #f59e0b; --text: #f8fafc; }}
        body, html {{ margin: 0; padding: 0; height: 100%; font-family: 'Inter', sans-serif; overflow: hidden; display: flex; flex-direction: column; background: var(--bg); color: var(--text); }}
        header {{ background: #000; padding: 0 24px; height: 65px; display: flex; align-items: center; justify-content: space-between; border-bottom: 3px solid var(--accent); z-index: 1000; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }}
        .brand {{ font-weight: 900; text-transform: uppercase; font-size: 1.1rem; letter-spacing: 1px; color: white; }}
        .main-content {{ display: flex; flex: 1; overflow: hidden; }}
        #map {{ flex: 1; background: #020617; }}
        .sidebar {{ width: 400px; background: var(--panel); border-left: 1px solid #1e293b; display: flex; flex-direction: column; }}
        .sidebar-header {{ padding: 24px; background: #000; border-bottom: 1px solid #1e293b; }}
        .search-input {{ width: 100%; padding: 14px; background: #1e293b; border: 1px solid #334155; color: white; border-radius: 8px; font-weight: 600; }}
        .pilot-list {{ flex: 1; overflow-y: auto; list-style: none; padding: 0; margin: 0; }}
        .pilot-item {{ padding: 20px 24px; border-bottom: 1px solid #1e293b; cursor: pointer; display: block; text-decoration: none; color: inherit; transition: 0.2s; }}
        .pilot-item:hover {{ background: #1e293b; }}
        .pilot-item.verified {{ background: #0f172a; border-left: 5px solid var(--accent); }}
        .p-name {{ display: block; font-weight: 800; font-size: 1.05rem; color: #fff; }}
        .p-loc {{ font-size: 0.8rem; color: #94a3b8; margin-top: 4px; }}
        .elite-tag {{ font-size: 0.6rem; background: var(--accent); color: #000; padding: 2px 6px; border-radius: 4px; font-weight: 900; display: inline-block; margin-top: 8px; }}
        @keyframes pulse {{ 0% {{ box-shadow: 0 0 0 0px rgba(245, 158, 11, 0.7); }} 70% {{ box-shadow: 0 0 0 10px rgba(245, 158, 11, 0); }} 100% {{ box-shadow: 0 0 0 0px rgba(245, 158, 11, 0); }} }}
        .radar-pulse {{ border-radius: 50%; animation: pulse 2s infinite; }}
        @media (max-width: 850px) {{ .main-content {{ flex-direction: column; }} .sidebar {{ width: 100%; height: 50%; border-left: none; }} #map {{ height: 50%; flex: none; }} }}
    </style>
</head>
<body>
<header>
    <div class="brand">{brand}</div>
    <div style="font-size:0.7rem; color:var(--accent); font-weight:800; display:flex; align-items:center; gap:8px;">
        <div style="width:8px; height:8px; background:var(--accent); border-radius:50%; box-shadow:0 0 8px var(--accent);"></div>
        {count} UNITS ACTIVE • {date}
    </div>
</header>
<div class="main-content">
    <div id="map"></div>
    <aside class="sidebar">
        <div class="sidebar-header"><input type="text" id="searchInput" class="search-input" placeholder="Search by City or State..." onkeyup="filterSidebar()"></div>
        <nav class="pilot-list" id="pilotList">{sidebar_items}</nav>
    </aside>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    var map = L.map('map', {{ zoomControl: false }}).setView([39.8283, -98.5795], 5);
    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png').addTo(map);
    var pilots = {json_data};
    pilots.forEach(p => {{
        var color = p.is_verified ? '#f59e0b' : '#475569';
        var className = p.is_verified ? 'radar-pulse' : '';
        var icon = L.divIcon({{ 
            className: className, 
            html: `<div style="background:${{color}}; width:10px; height:10px; border-radius:50%; border:2px solid white; box-shadow: 0 0 10px ${{color}};"></div>`, 
            iconSize: [12,12] 
        }});
        L.marker([p.lat, p.lng], {{icon: icon}}).addTo(map).bindPopup(`
            <div style="font-family:'Inter',sans-serif; padding:5px;">
                <b style="font-size:14px;">${{p.name}}</b><br><span style="color:#666;">${{p.city}}, ${{p.state}}</span><br><br>
                <a href="${{p.url}}" style="display:block; background:#000; color:#fff; padding:8px 12px; text-decoration:none; border-radius:4px; font-size:11px; text-align:center;">OPEN DOSSIER</a>
            </div>
        `);
    }});
    function filterSidebar() {{
        var input = document.getElementById("searchInput").value.toUpperCase();
        var items = document.getElementsByClassName("pilot-item");
        for (var i = 0; i < items.length; i++) {{ items[i].style.display = items[i].textContent.toUpperCase().indexOf(input) > -1 ? "" : "none"; }}
    }}
</script>
</body>
</html>
"""

profile_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{name} | {brand}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; background: #020617; color: #f8fafc; padding: 20px; }}
        .container {{ max-width: 800px; margin: 40px auto; background: #0f172a; padding: 50px; border-radius: 12px; border: 1px solid #1e293b; border-top: 10px solid {accent}; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }}
        .elite-badge {{ background: var(--accent); color: #000; padding: 8px 16px; border-radius: 4px; font-weight: 900; display: {show_verified}; margin-bottom: 24px; width: fit-content; font-size: 0.8rem; letter-spacing: 1px; }}
        h1 {{ margin: 0; font-size: 3rem; letter-spacing: -2px; color: #fff; }}
        .location-meta {{ color: #94a3b8; font-size: 1.1rem; margin-bottom: 30px; font-weight: 600; }}
        .spec-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; margin: 30px 0; }}
        .spec-card {{ background: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #334155; text-align: center; }}
        .spec-label {{ color: #64748b; font-size: 0.65rem; text-transform: uppercase; font-weight: 800; display: block; margin-bottom: 5px; }}
        .spec-value {{ font-weight: 900; color: #fff; font-size: 1rem; }}
        .cta-btn {{ display: block; background: {accent}; color: #000; padding: 20px; text-align: center; font-weight: 900; text-decoration: none; border-radius: 8px; font-size: 1.25rem; margin-top: 40px; transition: 0.2s; }}
        .cta-btn:hover {{ transform: scale(1.02); }}
    </style>
</head>
<body>
    <div class="container">
        <nav><a href="../index.html" style="color:var(--accent); text-decoration:none; font-weight:900; font-size:0.8rem;">&larr; BACK TO MISSION CONTROL</a></nav>
        <div class="elite-badge" style="margin-top:24px;">ELITE UNIT VERIFIED</div>
        <h1>{name}</h1>
        <div class="location-meta">{city}, {state} &bull; Operational Unit</div>
        <div class="spec-grid">
            <div class="spec-card"><span class="spec-label">Unit Status</span><span class="spec-value" style="color:#22c55e;">READY</span></div>
            <div class="spec-card"><span class="spec-label">Service Area</span><span class="spec-value">{state}</span></div>
            <div class="spec-card"><span class="spec-label">Hardware Tier</span><span class="spec-value">Industrial</span></div>
            <div class="spec-card"><span class="spec-label">Vetting Score</span><span class="spec-value">98/100</span></div>
        </div>
        <div style="border-top: 1px solid #1e293b; padding-top:30px; line-height:1.8;">{bio}</div>
        <a href="tel:{phone}" class="cta-btn">INITIALIZE CONTACT DISPATCH: {phone}</a>
    </div>
</body>
</html>
"""

def run_build():
    if not os.path.exists("pilot"): os.makedirs("pilot")
    map_data, s_v, s_s = [], "", ""
    sitemap_entries = [f"{DOMAIN}/index.html"]
    
    try:
        with open(DB_FILE, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                f, l = row.get('First Name', '').strip(), row.get('Last Name', '').strip()
                name, city, state = f"{f} {l}", row.get('city', '').strip(), row.get('state', '').strip()
                biz, phone, email = row.get('Business', '').strip() or "Standard Unit", row.get('Phone', '').strip(), row.get('Email', '').strip()
                is_e = "lokedrone" in biz.lower() or "lokedrone" in email.lower() or "loke" in name.lower()
                
                slug = clean_slug(f"{name}-{city}-{state}")
                url = f"pilot/{slug}.html"
                sitemap_entries.append(f"{DOMAIN}/{url}")
                
                lat, lng = row.get('latitude'), row.get('longitude')
                if lat and lng and str(lat) != 'nan' and str(lat) != '':
                    map_data.append({"name":name,"lat":float(lat)+get_jitter(),"lng":float(lng)+get_jitter(),"city":city,"state":state,"url":url,"is_verified":is_e})

                item = f'<a href="{url}" class="pilot-item {"verified" if is_e else ""}"><span class="p-name">{name}</span><span class="p-loc">{city}, {state}</span>'
                if is_e: item += '<span class="elite-tag">Elite Verified</span>'
                item += '</a>'
                if is_e: s_v += item
                else: s_s += item

                with open(url, "w", encoding="utf-8") as p:
                    p.write(profile_template.format(name=name, city=city, state=state, brand=BRAND_NAME, business=biz, bio=row.get('Bio','Unit ready for mission deployment.'), phone=phone, email=email, accent="#f59e0b" if is_e else "#334155", show_verified="block" if is_e else "none", show_unverified="none" if is_e else "block"))

    except Exception as e:
        print(f"Build Error: {e}")
        return

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html.format(brand=BRAND_NAME, tagline=TAGLINE, count=len(map_data), date=CURRENT_DATE, json_data=json.dumps(map_data), sidebar_items=s_v + s_s))

    with open("sitemap.xml", "w", encoding="utf-8") as sm:
        sm.write('<?xml version="1.0" encoding="UTF-8"?>\\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\\n')
        for entry in sitemap_entries:
            sm.write(f'  <url><loc>{entry}</loc><lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod></url>\\n')
        sm.write('</urlset>')

    print("BUILD COMPLETE: System Optimized.")

if __name__ == "__main__":
    run_build()