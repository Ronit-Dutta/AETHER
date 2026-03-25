"""Quick check of what's in the database."""
from database import get_client, get_all_planets, get_mission_logs

sb = get_client()
planets = get_all_planets(sb, limit=5)
logs = get_mission_logs(sb, limit=3)

print(f"Planets in DB: {len(planets)}")
for p in planets[:5]:
    name = p.get("pl_name", "?")
    score = p.get("habitability_score", "?")
    ptype = p.get("planet_type", "?")
    print(f"  {name} | Score: {score}% | Type: {ptype}")

print(f"\nMission logs: {len(logs)}")
for l in logs:
    status = l.get("status", "?")
    scanned = l.get("planets_scanned", 0)
    new = l.get("planets_new", 0)
    reports = l.get("bio_reports_generated", 0)
    print(f"  {status} | Scanned: {scanned} | New: {new} | Reports: {reports}")
