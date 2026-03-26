import os
import sys

# Ensure the backend directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database import get_client, seed_research_papers
except ImportError:
    # If run from root
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    from database import get_client, seed_research_papers

def main():
    print("--- AETHER DATABASE SEEDER ---")
    supabase = get_client()
    if not supabase:
        print("Failed to connect to Supabase.")
        return
        
    print("Seeding Research Papers...")
    seed_research_papers(supabase)
    print("Done!")

if __name__ == "__main__":
    main()
