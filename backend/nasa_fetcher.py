"""
NASA Exoplanet Archive Data Fetcher
Connects to NASA's TAP (Table Access Protocol) API to retrieve
the latest confirmed exoplanet discoveries.
"""
import requests
import json
from datetime import datetime, timedelta


NASA_TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"


def fetch_recent_exoplanets(days_back=30, limit=50):
    """
    Fetch recently confirmed exoplanets from NASA's Exoplanet Archive.
    Uses the TAP (Table Access Protocol) with ADQL queries.
    
    Args:
        days_back: Number of days to look back for new discoveries
        limit: Maximum number of results to return
    
    Returns:
        List of dictionaries containing exoplanet data
    """
    # ADQL query to fetch confirmed planets with key parameters
    query = f"""
    SELECT TOP {limit}
        pl_name, hostname, discoverymethod, disc_year, disc_facility,
        pl_orbper, pl_orbsmax, pl_rade, pl_bmasse, pl_eqt,
        pl_orbeccen, pl_insol,
        st_teff, st_rad, st_mass, st_lum, st_spectype,
        sy_dist, sy_vmag,
        rowupdate
    FROM ps
    WHERE default_flag = 1
    ORDER BY rowupdate DESC
    """

    params = {
        "query": query,
        "format": "json"
    }

    try:
        response = requests.get(NASA_TAP_URL, params=params, timeout=30)
        response.raise_for_status()
        planets = response.json()
        
        print(f"[NASA] Fetched {len(planets)} exoplanets from NASA Archive")
        return planets
    except requests.exceptions.RequestException as e:
        print(f"[NASA] Error fetching data: {e}")
        return []


def fetch_planet_details(planet_name):
    """
    Fetch detailed information for a specific exoplanet by name.
    
    Args:
        planet_name: The official name of the exoplanet (e.g., 'Kepler-442 b')
    
    Returns:
        Dictionary with planet details or None
    """
    query = f"""
    SELECT
        pl_name, hostname, discoverymethod, disc_year, disc_facility,
        pl_orbper, pl_orbsmax, pl_rade, pl_bmasse, pl_bmassj,
        pl_eqt, pl_orbeccen, pl_insol, pl_dens,
        st_teff, st_rad, st_mass, st_lum, st_spectype, st_age,
        st_met, st_metratio,
        sy_dist, sy_vmag, sy_kmag,
        rowupdate
    FROM ps
    WHERE default_flag = 1 AND pl_name = '{planet_name}'
    """

    params = {
        "query": query,
        "format": "json"
    }

    try:
        response = requests.get(NASA_TAP_URL, params=params, timeout=30)
        response.raise_for_status()
        results = response.json()
        
        if results:
            return results[0]
        return None
    except requests.exceptions.RequestException as e:
        print(f"[NASA] Error fetching planet details: {e}")
        return None


def get_discovery_stats():
    """
    Fetch overall discovery statistics from the archive.
    Returns total counts by discovery method and year.
    """
    query = """
    SELECT discoverymethod, disc_year, COUNT(*) as count
    FROM ps
    WHERE default_flag = 1
    GROUP BY discoverymethod, disc_year
    ORDER BY disc_year DESC, count DESC
    """
    
    params = {
        "query": query,
        "format": "json"
    }

    try:
        response = requests.get(NASA_TAP_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[NASA] Error fetching stats: {e}")
        return []


if __name__ == "__main__":
    # Quick test
    planets = fetch_recent_exoplanets(days_back=90, limit=5)
    for p in planets:
        print(f"  🪐 {p.get('pl_name', 'Unknown')} | "
              f"Radius: {p.get('pl_rade', '?')} Earth | "
              f"Temp: {p.get('pl_eqt', '?')} K | "
              f"Updated: {p.get('rowupdate', '?')}")
