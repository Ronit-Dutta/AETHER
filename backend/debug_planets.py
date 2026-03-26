import os
import sys
from database import get_client

def check_planets():
    supabase = get_client()
    result = supabase.table("planets").select("pl_name, short_description").order("created_at", desc=True).limit(5).execute()
    print(f"Latest 5 Planets:")
    for planet in result.data:
        print(f"Name: {planet['pl_name']}")
        print(f"Desc: {planet['short_description']}")
        print("-" * 20)

if __name__ == "__main__":
    check_planets()
