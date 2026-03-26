import os
import sys
from database import get_client

def check_research():
    supabase = get_client()
    result = supabase.table("research_papers").select("*").execute()
    print(f"Total Research Papers: {len(result.data)}")
    for paper in result.data:
        print(f"- {paper['title']}")

if __name__ == "__main__":
    check_research()
