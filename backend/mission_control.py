"""
AETHER Mission Orchestrator
The main script that runs the complete mission cycle:
1. Fetch new exoplanets from NASA
2. Calculate habitability for each
3. Generate AI bio-reports via Gemini
4. Store everything in Supabase

This script is designed to be run daily via GitHub Actions.
"""
import sys
import time
import json
from datetime import datetime

from nasa_fetcher import fetch_recent_exoplanets
from habitability_engine import generate_planet_profile
from gemini_engine import generate_bio_report, generate_planet_description
from database import (
    get_client, upsert_planet, save_bio_report,
    log_mission, complete_mission, get_existing_planet_names
)


def run_mission(limit=50, generate_reports=True):
    """
    Execute a full AETHER mission cycle.
    
    Args:
        limit: Max number of planets to process
        generate_reports: Whether to generate AI bio-reports (uses Gemini API credits)
    """
    print("=" * 70)
    print(f"  🛸 AETHER MISSION CONTROL — INITIATING SCAN")
    print(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70)
    
    # Initialize database client
    supabase = get_client()
    mission_id = log_mission(supabase, "daily_audit")
    
    errors = []
    planets_new = 0
    planets_updated = 0
    reports_generated = 0
    
    # Get existing planets to detect new discoveries
    existing_names = get_existing_planet_names(supabase)

    # Step 1: Fetch from NASA
    print("\n📡 PHASE 1: Scanning NASA Exoplanet Archive...")
    # Fetch a large chunk to ensure we find enough new ones
    raw_planets_all = fetch_recent_exoplanets(limit=10000)
    
    if not raw_planets_all:
        print("❌ No data received from NASA. Aborting mission.")
        if mission_id:
            complete_mission(supabase, mission_id, 0, 0, 0, 0, ["No data from NASA"])
        return
        
    raw_planets = []
    for p in raw_planets_all:
        if p.get("pl_name") not in existing_names:
            raw_planets.append(p)
        if len(raw_planets) >= limit:
            break
            
    print(f"   ✅ Discovered {len(raw_planets)} NEW planetary records from {len(raw_planets_all)} scanned\n")
    
    # Step 2 & 3: Process each planet
    print("🔬 PHASE 2: Habitability Analysis & Intelligence Report Generation...")
    
    for i, raw_planet in enumerate(raw_planets, 1):
        planet_name = raw_planet.get("pl_name", "Unknown")
        is_new = planet_name not in existing_names
        status = "🆕 NEW" if is_new else "🔄 UPDATE"
        
        print(f"\n   [{i}/{len(raw_planets)}] {status}: {planet_name}")
        
        try:
            # Calculate habitability
            profile = generate_planet_profile(raw_planet)
            hab = profile["habitability"]
            print(f"      Score: {hab['score']}% ({hab['classification']}) | "
                  f"Type: {profile['planet_type']['icon']} {profile['planet_type']['type']}")
            
            # Generate AI content
            short_desc = None
            bio_report = None
            
            if generate_reports:
                # Generate short description
                short_desc = generate_planet_description(profile)
                
                # Generate full bio-report only for interesting planets or new ones
                if is_new or hab["score"] >= 25:
                    bio_report = generate_bio_report(profile)
                    if bio_report and "error" not in bio_report:
                        reports_generated += 1
                        # Save to audit log
                        save_bio_report(supabase, planet_name, bio_report)
                    
                    # Rate limiting: be respectful to Gemini API
                    time.sleep(1)
            
            # Save to database
            upsert_planet(supabase, profile, short_desc, bio_report)
            
            if is_new:
                planets_new += 1
            else:
                planets_updated += 1
                
        except Exception as e:
            error_msg = f"Error processing {planet_name}: {str(e)}"
            print(f"      ❌ {error_msg}")
            errors.append(error_msg)
    
    # Complete mission log
    total_scanned = len(raw_planets_all)
    if mission_id:
        complete_mission(supabase, mission_id, total_scanned, planets_new, planets_updated, reports_generated, errors)
    
    # Final report
    print("\n" + "=" * 70)
    print("  🏁 MISSION COMPLETE")
    print(f"  📊 Scanned: {total_scanned} | New: {planets_new} | Updated: {planets_updated}")
    print(f"  🧬 Bio-Reports Generated: {reports_generated}")
    if errors:
        print(f"  ⚠️  Errors: {len(errors)}")
    print("=" * 70)


if __name__ == "__main__":
    # Parse arguments
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    reports = "--no-reports" not in sys.argv
    
    run_mission(limit=limit, generate_reports=reports)
