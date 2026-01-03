import pandas as pd
import os

# --- CONFIGURATION ---
INPUT_FILE = "final_leads_geocoded.csv"
OUTPUT_FILE = "final_leads_tagged.csv"

def run_tagger():
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: Could not find {INPUT_FILE}")
        return

    print("--- STARTING SMART TAGGER (V2) ---")
    df = pd.read_csv(INPUT_FILE)
    
    # Ensure columns exist and handle NaNs
    cols_to_clean = ['Industry', 'Equipment_Details', 'Name', 'RegistrantType', 'Deer_Recovery', 'Pet_Recovery']
    for col in cols_to_clean:
        if col not in df.columns: df[col] = ''
        df[col] = df[col].fillna('').astype(str)

    def get_tags(row):
        # 1. Start with any existing tags (cleaned)
        existing = row['Industry'].replace(';', ',').split(',')
        tags = [t.strip() for t in existing if t.strip()]
        
        # Prepare data for checking
        name_lower = row['Name'].lower()
        equip_upper = row['Equipment_Details'].upper()
        reg_type_lower = row['RegistrantType'].lower()

        # --- RULE 1: AGRICULTURE (The Strongest Indicator) ---
        # If they fly crop sprayers, they are Ag. Period.
        ag_drones = ['AGRAS', 'T40', 'T30', 'T10', 'T20', 'T50', 'XAG', 'H520', 'SPRAY']
        ag_keywords = ['ag ', 'farm', 'crop', 'agriculture', 'spraying', 'aerial application']
        
        is_ag = False
        if any(d in equip_upper for d in ag_drones) or any(k in name_lower for k in ag_keywords):
            tags.append("Agriculture")
            is_ag = True

        # --- RULE 2: THERMAL / INSPECTION ---
        thermal_drones = ['3T', '30T', 'H20T', 'XT2', 'XT', 'THERMAL', 'MAVIC 2 ENTERPRISE', 'M2EA', 'AUTEL EVO II DUAL', 'M30T']
        if any(d in equip_upper for d in thermal_drones) or 'thermal' in name_lower:
            tags.append("Thermal")
            tags.append("Inspection")

        # --- RULE 3: GOVERNMENT / PUBLIC SAFETY ---
        govt_keywords = ['police', 'sheriff', 'fire dept', 'city of', 'county of', 'department of', 'public safety', 'state of', 'university', 'college']
        if reg_type_lower == 'government' or any(k in name_lower for k in govt_keywords):
            tags.append("Government")
            if 'university' not in name_lower and 'college' not in name_lower:
                tags.append("Public Safety")

        # --- RULE 4: DEFENSE (Strict Mode) ---
        # Only tag Defense if it's NOT Ag, and has specific keywords
        # Removed "Systems", "Solutions", "Tactical" to prevent false positives
        defense_keywords = ['defense', 'aerospace', 'lockheed', 'northrop', 'raytheon', 'boeing', 'general atomics', 'l3harris']
        
        if not is_ag: # Farmers are rarely Defense contractors
            if any(k in name_lower for k in defense_keywords):
                tags.append("Defense")

        # --- RULE 5: RECOVERY (From Columns) ---
        if row['Deer_Recovery'].lower() == 'yes': tags.append("Deer Recovery")
        if row['Pet_Recovery'].lower() == 'yes': tags.append("Pet Recovery")

        # Clean up: Unique tags only, title case
        unique_tags = list(set(tags))
        # Remove 'Other' or 'Pending' if we found better tags
        if len(unique_tags) > 1 and 'Other' in unique_tags: unique_tags.remove('Other')
        
        return ", ".join(unique_tags)

    print("Retagging pilots with strict logic...")
    df['Industry'] = df.apply(get_tags, axis=1)

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"SUCCESS: Retagged {len(df)} pilots. Saved to {OUTPUT_FILE}")
    print("Now: Rename this file to 'final_leads_geocoded.csv' and run build_site.py")

if __name__ == "__main__":
    run_tagger()