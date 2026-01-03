import pandas as pd
import os

# --- CONFIGURATION ---
INPUT_FILE = "final_leads_geocoded.csv" # The one you just geocoded
OUTPUT_FILE = "final_leads_tagged.csv"

def run_tagger():
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: Could not find {INPUT_FILE}")
        return

    print("--- STARTING AUTO-TAGGER ---")
    df = pd.read_csv(INPUT_FILE)
    
    # Ensure columns exist
    if 'Industry' not in df.columns:
        df['Industry'] = ''
    
    # fill NaN with empty string to avoid errors
    df['Industry'] = df['Industry'].fillna('')
    df['Equipment_Details'] = df['Equipment_Details'].fillna('')
    df['Name'] = df['Name'].fillna('')
    df['RegistrantType'] = df['RegistrantType'].fillna('')

    def get_tags(row):
        # Start with existing industry
        tags = [str(row['Industry'])]
        
        # 1. DEER RECOVERY (From 'Deer_Recovery' column)
        if str(row.get('Deer_Recovery', '')).lower() == 'yes':
            tags.append("Deer Recovery")
            
        # 2. PET RECOVERY (From 'Pet_Recovery' column)
        if str(row.get('Pet_Recovery', '')).lower() == 'yes':
            tags.append("Pet Recovery")

        # 3. GOVERNMENT (From Name or RegistrantType)
        name_lower = row['Name'].lower()
        reg_type = str(row['RegistrantType']).lower()
        govt_keywords = ['police', 'sheriff', 'fire dept', 'city of', 'county of', 'department of', 'public safety', 'state of']
        
        if reg_type == 'government' or any(k in name_lower for k in govt_keywords):
            tags.append("Government")
            tags.append("Public Safety")

        # 4. DEFENSE (From Name)
        defense_keywords = ['defense', 'aerospace', 'tactical', 'systems', 'solutions', 'lockheed', 'northrop', 'raytheon']
        if any(k in name_lower for k in defense_keywords):
            tags.append("Defense")

        # 5. THERMAL / INSPECTION (From Equipment)
        # Scan fleet for thermal cameras
        equip = str(row['Equipment_Details']).upper()
        thermal_gear = ['3T', '30T', 'H20T', 'XT2', 'XT', 'THERMAL', 'MAVIC 2 ENTERPRISE DUAL', 'M2EA', 'AUTEL EVO II DUAL']
        
        if any(gear in equip for gear in thermal_gear):
            tags.append("Thermal")
            tags.append("Inspection")
            
        # 6. AGRICULTURE (From Equipment or Name)
        ag_gear = ['AGRAS', 'T40', 'T30', 'T10', 'T20', 'SPRAY']
        if any(gear in equip for gear in ag_gear) or 'ag ' in name_lower or 'farm' in name_lower:
            tags.append("Agriculture")

        # Clean up tags: Join them unique, comma separated
        # e.g. "Agriculture, Thermal, Deer Recovery"
        unique_tags = list(set([t.strip() for t in tags if t.strip()]))
        return ", ".join(unique_tags)

    # Apply the logic
    print("Scanning fleet data and assigning tags...")
    df['Industry'] = df.apply(get_tags, axis=1)

    # Save
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"SUCCESS: Tagged {len(df)} pilots. Saved to {OUTPUT_FILE}")
    print("Next: Rename this file to 'final_leads_geocoded.csv' and run build_site.py")

if __name__ == "__main__":
    run_tagger()