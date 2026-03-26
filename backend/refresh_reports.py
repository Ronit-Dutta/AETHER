"""
Utility to refresh AI reports for existing planets in the database.
Run this to fix 'Atmospheric data pending' generic descriptions.
"""
import os
import sys
import time
from database import get_client, upsert_planet, get_all_planets, save_bio_report
from habitability_engine import generate_planet_profile
from gemini_engine import generate_bio_report, generate_planet_description

def refresh_reports(limit=10):
    print("--- AETHER REPORT REFRESHER ---")
    supabase = get_client()
    if not supabase:
        return
        
    # Fetch planets that need updating
    # We look for those with the fallback string or missing reports
    print(f"Scanning for planets needing report updates (limit {limit})...")
    result = supabase.table("planets").select("*").execute()
    all_planets = result.data
    
    planets_to_fix = []
    for p in all_planets:
        desc = p.get("short_description") or ""
        # Check if it's the fallback
        is_fallback = "Atmospheric data pending" in desc or desc == "{}" or not desc
        is_missing_bio = not p.get("bio_report") or "error" in str(p.get("bio_report"))
        
        if is_fallback or is_missing_bio:
            planets_to_fix.append(p)
            
    print(f"Found {len(planets_to_fix)} planets needing better intelligence reports.")
    
    count = 0
    for p in planets_to_fix[:limit]:
        name = p.get("pl_name")
        print(f"\n[{count+1}/{limit}] Refreshing intelligence for {name}...")
        
        try:
            # Reconstruct the profile from DB data (which has NASA fields)
            profile = generate_planet_profile(p)
            
            # Generate new AI content
            print("   - Generating discovery description...")
            short_desc = generate_planet_description(profile)
            
            print("   - Generating bio-report...")
            bio_report = generate_bio_report(profile)
            
            # Save
            upsert_planet(supabase, profile, short_desc, bio_report)
            if bio_report and "error" not in bio_report:
                save_bio_report(supabase, name, bio_report)
                
            print(f"   ✅ {name} updated with unique intelligence.")
            count += 1
            time.sleep(1.5) # Rate limiting
            
        except Exception as e:
            print(f"   ❌ Error updating {name}: {e}")

    print(f"\n--- Refresh Complete: {count} planets updated ---")

if __name__ == "__main__":
    refresh_reports(limit=5)
