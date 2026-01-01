import pandas as pd
from geopy.geocoders import Nominatim
import time

# CONFIGURATION
input_file = "drone_pilots_WITH_PHONES_FINAL.csv"

# LOAD DATA
print(f"Reading {input_file}...")
try:
    df = pd.read_csv(input_file)
except FileNotFoundError:
    print("❌ Error: CSV file not found.")
    exit()

# SETUP GEOLOCATOR
geolocator = Nominatim(user_agent="drone_pilot_locator_round2")

def get_smart_location(row):
    # 1. If we already have good coordinates, keep them!
    current_coords = str(row.get('Coordinates', '0,0'))
    if current_coords != "0,0" and "," in current_coords:
        return current_coords

    # 2. Get City and State
    city = str(row.get('City', '')).replace("nan", "").strip()
    state = str(row.get('State', '')).replace("nan", "").strip()

    # 3. Try Specific: "City, State, USA"
    if city and state:
        search_query = f"{city}, {state}, USA"
        try:
            location = geolocator.geocode(search_query, timeout=10)
            if location:
                print(f"✅ Fixed: {search_query}")
                return f"{location.latitude}, {location.longitude}"
        except:
            pass # If it fails, just move to the next step
        
        # PAUSE (to be polite to the server)
        time.sleep(1)

    # 4. FALLBACK: Try Generic "State, USA" (So they at least show up!)
    if state:
        search_query = f"{state}, USA"
        try:
            location = geolocator.geocode(search_query, timeout=10)
            if location:
                print(f"⚠️  State-Level Match: {search_query}")
                return f"{location.latitude}, {location.longitude}"
        except:
            pass

    print(f"❌ Failed: {city}, {state}")
    return "0,0"

print("------------------------------------------------")
print(f"🚀 Starting Round 2 Repairs on {len(df)} pilots...")
print("------------------------------------------------")

# Run the smart locator
df['Coordinates'] = df.apply(get_smart_location, axis=1)

# Save
df.to_csv(input_file, index=False)
print("------------------------------------------------")
print("🎉 REPAIR COMPLETE.")
print("All pilots should now have coordinates (at least state-level).")