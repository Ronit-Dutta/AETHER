import os
import sys
import json
import traceback

# Ensure the backend directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from gemini_engine import generate_planet_description
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    from gemini_engine import generate_planet_description

def test_gemini():
    print("--- GEMINI ENGINE TEST ---")
    planet = {
        "name": "Kepler-186 f",
        "planet_type": {"type": "Terrestrial"},
        "equilibrium_temp_k": 188,
        "radius_earth": 1.17,
        "distance_ly": 582,
        "habitability": {"score": 65, "classification": "Promising"}
    }
    
    print(f"Generating report for {planet['name']}...")
    try:
        report = generate_planet_description(planet)
        print("\nResult:")
        print(report)
        
        data = json.loads(report)
        print("\nSuccess: JSON is valid.")
        print(f"Weather: {data.get('weather')}")
        print(f"Life Probability: {data.get('life_probability')}")
    except Exception as e:
        print(f"\nCaught Exception in test script:")
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini()
