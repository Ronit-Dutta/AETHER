import os
import sys
import time
from database import get_client, get_all_planets, upsert_planet
from gemini_engine import generate_planet_description
from habitability_engine import generate_planet_profile

def update_top_planets(limit=10):
    supabase = get_client()
    planets = get_all_planets(supabase, limit=limit)
    print(f"Refreshing top {len(planets)} planets with new AI insights...")
    
    for i, p in enumerate(planets, 1):
        name = p.get("pl_name")
        print(f"[{i}/{len(planets)}] Updating {name}...")
        
        # Profile needs to be regenerated to have all fields for Gemini
        profile = generate_planet_profile(p)
        
        try:
            new_desc = generate_planet_description(profile)
            # Update only the description in the DB
            supabase.table("planets").update({"short_description": new_desc}).eq("pl_name", name).execute()
            print(f"      Success.")
        except Exception as e:
            print(f"      Failed: {e}")
        
        # Rate limit protection
        time.sleep(2)

if __name__ == "__main__":
    update_top_planets(5)
