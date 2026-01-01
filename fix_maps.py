import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

# FILE CONFIGURATION
input_file = "drone_pilots_WITH_PHONES_FINAL.csv"

print(f"Reading {input_file}...")
try:
    df = pd.read_csv(input_file)
except FileNotFoundError:
    print("❌ Error: CSV file not found. Make sure this script is in the same folder as your CSV.")
    exit()

# Initialize Geolocator
geolocator = Nominatim(user_agent="drone_pilot_locator_v1")

def get_location(row):
    # If coordinates already exist, skip
    if 'Coordinates' in row and pd.notna(row['Coordinates']) and row['Coordinates'] != "0,0":
        return row['Coordinates']
    
    city = str(row.get('City', '')).strip()
    state = str(row.get('State', '')).strip()
    
    if not city or not state:
        return "0,0"

    address = f"{city}, {state}, USA"
    try:
        location = geolocator.geocode(address, timeout=10)
        if location:
            print(f"Found: {address} -> {location.latitude}, {location.longitude}")
            return f"{location.latitude}, {location.longitude}"
    except:
        time.sleep(1)
            
    print(f"Not Found: {address}")
    return "0,0"

print("------------------------------------------------")
print(f"Locating {len(df)} pilots. This will take about 5-6 minutes...")
print("------------------------------------------------")

# Apply the locator (with a pause to be polite to the server)
df['Coordinates'] = df.apply(lambda row: (time.sleep(1), get_location(row))[1], axis=1)

# Save the new file
df.to_csv(input_file, index=False)
print("------------------------------------------------")
print("DONE! Coordinates added to your CSV file.")