"""
AETHER Backend Configuration
Loads environment variables and provides centralized config access.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# NASA
NASA_EXOPLANET_API = os.getenv("NASA_EXOPLANET_API", "https://exoplanetarchive.ipac.caltech.edu/TAP/sync")
