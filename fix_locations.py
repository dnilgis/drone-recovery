import pandas as pd
from geopy.geocoders import ArcGIS
from tqdm import tqdm
import os
import signal
import sys

# --- CONFIGURATION ---
INPUT_FILE = "final_leads_consolidated.csv"
OUTPUT_FILE = "final_leads_geocoded.csv"

# Global dataframe for safe saving
df = None

def save_and_exit(signum=None, frame=None):
    global df
    if df is not None:
        print("\n\nStopping... Saving progress...")
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"Saved to {OUTPUT_FILE}")
    sys.exit(0)

def run_fixer():
    global df
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: Could not find {INPUT_FILE}")
        return

    print("--- STARTING ARCGIS HACKER FIXER ---")
    print("Using Esri servers. This should be much faster and stable.")
    
    # 1. Load Data
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} pilots.")

    # 2. Setup ArcGIS (The Secret Weapon)
    # No API key needed, no user_agent needed, very robust.
    geolocator = ArcGIS()

    # 3. Define the cleaning function
    def fix_row(row):
        # Skip if already fixed
        if "City (Fixed)" in str(row.get('GeoAccuracy', '')):
             return row['Latitude'], row['Longitude'], row['GeoAccuracy']

        # Construct address
        # We try strict address first, then fallback to City/State
        address = f"{row['Street']}, {row['City']}, {row['State']}"
        
        try:
            location = geolocator.geocode(address, timeout=10)
            if location:
                return location.latitude, location.longitude, "City (Fixed)"
            else:
                # Fallback to just City/State if Street fails
                address_simple = f"{row['City']}, {row['State']}"
                location = geolocator.geocode(address_simple, timeout=10)
                if location:
                    return location.latitude, location.longitude, "City (Fixed)"
        except Exception:
            pass
        
        # If all fails, keep old data
        return row['Latitude'], row['Longitude'], row.get('GeoAccuracy', 'State')

    # Register save-on-exit
    signal.signal(signal.SIGINT, save_and_exit)

    # 4. Run the loop
    print("Fixing locations... (Press Ctrl+C to stop)")
    tqdm.pandas(desc="Geocoding")
    
    df[['Latitude', 'Longitude', 'GeoAccuracy']] = df.apply(
        lambda row: pd.Series(fix_row(row)), axis=1
    )

    # 5. Final Save
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSUCCESS! Fixed data saved to: {OUTPUT_FILE}")
    print("Rename this file to final_leads_consolidated.csv and run build_site.py")

if __name__ == "__main__":
    run_fixer()