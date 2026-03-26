"""
Supabase Database Client for Project AETHER
Handles all database operations: storing planet data, bio-reports,
and retrieving data for the frontend dashboard.
"""
import json
from datetime import datetime, timezone
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY


def get_client() -> Client:
    """Create and return a Supabase client instance."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ─── SQL for table creation (run once via Supabase SQL Editor) ───
INIT_SQL = """
-- Enable pgvector extension for RAG
CREATE EXTENSION IF NOT EXISTS vector;

-- Main planets table
CREATE TABLE IF NOT EXISTS planets (
    id BIGSERIAL PRIMARY KEY,
    pl_name TEXT UNIQUE NOT NULL,
    host_star TEXT,
    discovery_method TEXT,
    discovery_year INTEGER,
    discovery_facility TEXT,
    
    -- Physical parameters
    radius_earth DOUBLE PRECISION,
    mass_earth DOUBLE PRECISION,
    equilibrium_temp_k DOUBLE PRECISION,
    orbital_period_days DOUBLE PRECISION,
    orbital_distance_au DOUBLE PRECISION,
    eccentricity DOUBLE PRECISION,
    insolation_flux DOUBLE PRECISION,
    
    -- Stellar parameters
    star_temp_k DOUBLE PRECISION,
    star_radius_solar DOUBLE PRECISION,
    star_mass_solar DOUBLE PRECISION,
    star_spectral_type TEXT,
    
    -- Calculated fields
    distance_ly DOUBLE PRECISION,
    habitability_score INTEGER,
    habitability_classification TEXT,
    habitability_color TEXT,
    planet_type TEXT,
    planet_type_icon TEXT,
    planet_type_description TEXT,
    habitable_zone_inner DOUBLE PRECISION,
    habitable_zone_outer DOUBLE PRECISION,
    
    -- Habitability breakdown (JSON)
    habitability_breakdown JSONB,
    
    -- AI-generated content
    short_description TEXT,
    bio_report JSONB,
    
    -- Metadata
    nasa_last_updated TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bio-reports audit log
CREATE TABLE IF NOT EXISTS bio_reports (
    id BIGSERIAL PRIMARY KEY,
    planet_name TEXT REFERENCES planets(pl_name),
    report_data JSONB NOT NULL,
    model_used TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Discovery stats cache
CREATE TABLE IF NOT EXISTS discovery_stats (
    id BIGSERIAL PRIMARY KEY,
    stat_type TEXT NOT NULL,
    stat_data JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Mission logs (tracks each automated run)
CREATE TABLE IF NOT EXISTS mission_logs (
    id BIGSERIAL PRIMARY KEY,
    run_type TEXT NOT NULL,
    planets_scanned INTEGER DEFAULT 0,
    planets_new INTEGER DEFAULT 0,
    planets_updated INTEGER DEFAULT 0,
    bio_reports_generated INTEGER DEFAULT 0,
    errors TEXT[],
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'running'
);

-- Research papers table
CREATE TABLE IF NOT EXISTS research_papers (
    id BIGSERIAL PRIMARY KEY,
    title TEXT UNIQUE NOT NULL,
    authors TEXT,
    publication_year INTEGER,
    journal TEXT,
    summary TEXT,
    url TEXT,
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_planets_score ON planets(habitability_score DESC);
CREATE INDEX IF NOT EXISTS idx_planets_updated ON planets(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_planets_type ON planets(planet_type);
CREATE INDEX IF NOT EXISTS idx_mission_logs_date ON mission_logs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_research_tags ON research_papers USING GIN (tags);

-- Row-Level Security (allow public read access for the frontend)
ALTER TABLE planets ENABLE ROW LEVEL SECURITY;
ALTER TABLE bio_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE discovery_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE mission_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_papers ENABLE ROW LEVEL SECURITY;

-- Policies for anonymous read access
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public read planets') THEN
        CREATE POLICY "Public read planets" ON planets FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public read bio_reports') THEN
        CREATE POLICY "Public read bio_reports" ON bio_reports FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public read discovery_stats') THEN
        CREATE POLICY "Public read discovery_stats" ON discovery_stats FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public read mission_logs') THEN
        CREATE POLICY "Public read mission_logs" ON mission_logs FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public read research_papers') THEN
        CREATE POLICY "Public read research_papers" ON research_papers FOR SELECT USING (true);
    END IF;
END $$;
"""


def upsert_planet(supabase: Client, planet_profile: dict, short_desc: str = None, bio_report: dict = None):
    """
    Insert or update a planet record in the database.
    Uses upsert on pl_name to avoid duplicates.
    
    Args:
        supabase: Supabase client
        planet_profile: Enriched profile from habitability_engine
        short_desc: AI-generated short description
        bio_report: AI-generated bio-report dictionary
    """
    hab = planet_profile.get("habitability", {})
    ptype = planet_profile.get("planet_type", {})
    hz = hab.get("habitable_zone")
    
    record = {
        "pl_name": planet_profile["name"],
        "host_star": planet_profile.get("host_star"),
        "discovery_method": planet_profile.get("discovery_method"),
        "discovery_year": planet_profile.get("discovery_year"),
        "discovery_facility": planet_profile.get("discovery_facility"),
        "radius_earth": planet_profile.get("radius_earth"),
        "mass_earth": planet_profile.get("mass_earth"),
        "equilibrium_temp_k": planet_profile.get("equilibrium_temp_k"),
        "orbital_period_days": planet_profile.get("orbital_period_days"),
        "orbital_distance_au": planet_profile.get("orbital_distance_au"),
        "eccentricity": planet_profile.get("eccentricity"),
        "insolation_flux": planet_profile.get("insolation_flux"),
        "star_temp_k": planet_profile.get("star_temp_k"),
        "star_radius_solar": planet_profile.get("star_radius_solar"),
        "star_mass_solar": planet_profile.get("star_mass_solar"),
        "star_spectral_type": planet_profile.get("star_spectral_type"),
        "distance_ly": planet_profile.get("distance_ly"),
        "habitability_score": hab.get("score"),
        "habitability_classification": hab.get("classification"),
        "habitability_color": hab.get("color"),
        "planet_type": ptype.get("type"),
        "planet_type_icon": ptype.get("icon"),
        "planet_type_description": ptype.get("description"),
        "habitable_zone_inner": hz[0] if hz else None,
        "habitable_zone_outer": hz[1] if hz else None,
        "habitability_breakdown": hab.get("breakdown"),
        "short_description": short_desc,
        "bio_report": bio_report,
        "nasa_last_updated": planet_profile.get("last_updated"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    # Remove None values to avoid overwriting with null
    record = {k: v for k, v in record.items() if v is not None}
    
    try:
        result = supabase.table("planets").upsert(
            record,
            on_conflict="pl_name"
        ).execute()
        print(f"[DB] Upserted planet: {planet_profile['name']}")
        return result
    except Exception as e:
        print(f"[DB] Error upserting planet {planet_profile['name']}: {e}")
        return None


def save_bio_report(supabase: Client, planet_name: str, report: dict, model: str = "gemini-2.0-flash"):
    """Save a bio-report to the audit log."""
    try:
        result = supabase.table("bio_reports").insert({
            "planet_name": planet_name,
            "report_data": report,
            "model_used": model,
        }).execute()
        print(f"[DB] Saved bio-report for: {planet_name}")
        return result
    except Exception as e:
        print(f"[DB] Error saving bio-report: {e}")
        return None


def log_mission(supabase: Client, run_type: str = "daily_audit"):
    """Start a new mission log entry. Returns the log ID."""
    try:
        result = supabase.table("mission_logs").insert({
            "run_type": run_type,
            "status": "running"
        }).execute()
        return result.data[0]["id"] if result.data else None
    except Exception as e:
        print(f"[DB] Error creating mission log: {e}")
        return None


def complete_mission(supabase: Client, log_id: int, scanned: int, new: int, updated: int, reports: int, errors: list = None):
    """Complete a mission log entry with final stats."""
    try:
        supabase.table("mission_logs").update({
            "planets_scanned": scanned,
            "planets_new": new,
            "planets_updated": updated,
            "bio_reports_generated": reports,
            "errors": errors or [],
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed"
        }).eq("id", log_id).execute()
        print(f"[DB] Mission {log_id} completed: {scanned} scanned, {new} new, {reports} reports")
    except Exception as e:
        print(f"[DB] Error completing mission log: {e}")


def get_all_planets(supabase: Client, order_by: str = "habitability_score", limit: int = 100):
    """Fetch all planets ordered by a specified column."""
    try:
        result = supabase.table("planets").select("*").order(
            order_by, desc=True
        ).limit(limit).execute()
        return result.data
    except Exception as e:
        print(f"[DB] Error fetching planets: {e}")
        return []


def get_planet_by_name(supabase: Client, name: str):
    """Fetch a single planet by name."""
    try:
        result = supabase.table("planets").select("*").eq("pl_name", name).single().execute()
        return result.data
    except Exception as e:
        print(f"[DB] Error fetching planet {name}: {e}")
        return None


def get_mission_logs(supabase: Client, limit: int = 20):
    """Fetch recent mission logs."""
    try:
        result = supabase.table("mission_logs").select("*").order(
            "started_at", desc=True
        ).limit(limit).execute()
        return result.data
    except Exception as e:
        print(f"[DB] Error fetching mission logs: {e}")
        return []


def get_existing_planet_names(supabase: Client):
    """Get a set of all planet names currently in the database."""
    try:
        result = supabase.table("planets").select("pl_name").execute()
        return {r["pl_name"] for r in result.data}
    except Exception as e:
        print(f"[DB] Error fetching planet names: {e}")
        return set()


def seed_research_papers(supabase: Client):
    """Seed initial research papers into the database."""
    papers = [
        {
            "title": "Analysis of Habitability and Stellar Habitable Zones from Observed Exoplanets",
            "authors": "T. Bozlar et al.",
            "publication_year": 2023,
            "journal": "MDPI / ArXiv",
            "summary": "This study examines over 5,500 confirmed exoplanets, evaluating their surface temperatures and host star classifications to determine their potential for habitability within circumstellar habitable zones.",
            "url": "https://arxiv.org/abs/2301.07132",
            "tags": ["habitability", "census", "statistical analysis"]
        },
        {
            "title": "Probing the Limits of Habitability: a Catalogue of Rocky Exoplanets in the Habitable Zone",
            "authors": "L. Kaltenegger et al.",
            "publication_year": 2024,
            "journal": "ScienceDaily / Cornell",
            "summary": "A comprehensive catalog of 45 rocky exoplanets found within their stars' habitable zones, utilizing data from the NASA Exoplanet Archive and ESA's Gaia mission.",
            "url": "https://arxiv.org/abs/2312.00055",
            "tags": ["rocky planets", "habitable zone", "catalogue"]
        },
        {
            "title": "The NASA Habitable Worlds Program: Astrobiological Potential of Icy Worlds",
            "authors": "NASA Science Mission Directorate",
            "publication_year": 2025,
            "journal": "NASA Technical Reports",
            "summary": "An exploration of the astrobiological potential of 'icy worlds' in our outer solar system, such as Europa and Titan, and their implications for outer exoplanetary systems.",
            "url": "https://science.nasa.gov/astrophysics/programs/habitable-worlds-observatory/",
            "tags": ["icy worlds", "astrobiology", "outer planets"]
        },
        {
            "title": "SPARCS: Star-Planet Activity Research CubeSat - Monitoring Low-Mass Stars",
            "authors": "Evgenya Shkolnik et al.",
            "publication_year": 2026,
            "journal": "Nature Astronomy",
            "summary": "Preliminary results from the SPARCS mission monitoring the flare activity of M-type red dwarfs to assess the long-term atmospheric stability of their orbiting planets.",
            "url": "https://arxiv.org/abs/2411.00000",
            "tags": ["stellar activity", "red dwarfs", "atmospheres"]
        },
        {
            "title": "Atmospheric Characterization of Gas Giants and Super-Earths with JWST",
            "authors": "K. Stevenson et al.",
            "publication_year": 2025,
            "journal": "The Astrophysical Journal",
            "summary": "Utilizing the James Webb Space Telescope to detect water vapor, carbon dioxide, and methane in the atmospheres of distant gas giants and super-Earths.",
            "url": "https://webbtelescope.org/contents/news-releases/2023/news-2023-146",
            "tags": ["JWST", "spectroscopy", "atmospheres"]
        }
    ]
    
    for paper in papers:
        try:
            supabase.table("research_papers").upsert(paper, on_conflict="title").execute()
            print(f"[DB] Seeded research paper: {paper['title']}")
        except Exception as e:
            print(f"[DB] Error seeding paper {paper['title']}: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("AETHER Database Setup SQL")
    print("=" * 60)
    print("\nCopy the SQL below and run it in your Supabase SQL Editor:")
    print(f"\n{INIT_SQL}")
