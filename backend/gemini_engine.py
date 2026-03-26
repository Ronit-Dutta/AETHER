"""
Gemini AI Speculative Evolution Engine
Uses Google's Gemini model to generate creative yet scientifically-grounded
speculation about hypothetical lifeforms on exoplanets.
"""
import json
from google import genai
from config import GEMINI_API_KEY


# Initialize the Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-flash-latest"


def extract_json(text):
    """Robustly extract JSON from AI response text."""
    import re
    import json
    
    # Try to find JSON block in the text
    json_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if json_match:
        json_text = json_match.group(1).strip()
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            # Try to fix common issues like trailing commas or missing braces
            pass
            
    # Fallback: clean up common markdown artifacts
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    
    if text.startswith("json"):
        text = text[4:].strip()
        
    try:
        return json.loads(text)
    except:
        return None


def generate_bio_report(planet_profile):
    """
    Generate a comprehensive speculative evolution bio-report for a planet.
    """
    hab = planet_profile.get("habitability", {})
    eq_temp = planet_profile.get("equilibrium_temp_k")
    radius = planet_profile.get("radius_earth")
    mass = planet_profile.get("mass_earth")
    planet_type = planet_profile.get("planet_type", {})
    star_temp = planet_profile.get("star_temp_k")
    distance_ly = planet_profile.get("distance_ly")
    insol = planet_profile.get("insolation_flux")
    hz = hab.get("habitable_zone")
    orbital_au = planet_profile.get("orbital_distance_au")

    prompt = f"""You are an expert astrobiologist and speculative evolution scientist for Project AETHER.
    Analyze this REAL NASA data for exoplanet "{planet_profile['name']}" and generate a speculative biology report.

    PLANETARY DATA:
    - Name: {planet_profile['name']} | Host: {planet_profile['host_star']}
    - Type: {planet_type.get('type', 'Unknown')} ({planet_type.get('description', '')})
    - Radius: {radius} Re | Mass: {mass} Me | Temp: {eq_temp} K
    - Insolation: {insol} | Habitable Zone: {f'{hz[0]}-{hz[1]} AU' if hz else 'Unknown'}
    - Habitability Score: {hab.get('score', 0)}% ({hab.get('classification', 'Unknown')})

    TASK:
    Generate a vivid, scientifically-grounded report including environment summary, atmosphere analysis, 
    surface conditions, and 3 specific hypothetical lifeforms (name, common name, description, adaptation, size, energy source).
    Also include a habitability assessment, mission recommendation, and one fun fact.

    IMPORTANT: 
    - Respond ONLY with a valid JSON object. 
    - DO NOT include markdown code fences or any other text.
    - Base all speculation on the physical data provided.
    """

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={"temperature": 0.8}
        )
        
        bio_report = extract_json(response.text)
        if not bio_report:
            raise ValueError("Failed to extract valid JSON from Gemini response")
            
        bio_report["generation_model"] = MODEL
        bio_report["planet_name"] = planet_profile["name"]
        
        print(f"[GEMINI] Bio-report generated for {planet_profile['name']}")
        return bio_report
        
    except Exception as e:
        print(f"[GEMINI] Error generating bio-report: {e}")
        return {
            "error": str(e),
            "planet_name": planet_profile["name"],
            "environment_summary": f"{planet_profile['name']} is a {planet_type.get('type', 'mysterious')} world that requires further high-resolution atmospheric data to characterize fully.",
            "hypothetical_lifeforms": []
        }


def generate_planet_description(planet_profile):
    """
    Generate a detailed description for the Discovery Card.
    """
    hab = planet_profile.get("habitability", {})
    eq_temp = planet_profile.get("equilibrium_temp_k")
    planet_type = planet_profile.get("planet_type", {})

    prompt = f"""You are a senior astrobiologist. Analyze {planet_profile['name']} and provide a structured discovery report.
    Data: Type: {planet_type.get('type')}, Temp: {eq_temp}K, Radius: {planet_profile.get('radius_earth')}x Earth, Habitability: {hab.get('score', 0)}%.

    Respond in JSON format:
    {{
        "weather": "1-2 lines summarizing atmospheric conditions.",
        "habitability_insight": "2-3 lines about surface/living conditions for life.",
        "life_probability": "Percentage (e.g. '75%')",
        "life_reasoning": "One-sentence scientific justification."
    }}
    Return ONLY valid JSON."""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={"temperature": 0.7}
        )
        
        json_data = extract_json(response.text)
        if json_data:
            import json
            return json.dumps(json_data)
            
        raise ValueError("No JSON object found in response")
    except Exception as e:
        print(f"[GEMINI] Error generating detailed description: {e}")
        import json
        return json.dumps({
            "weather": "Atmospheric data pending further spectroscopic analysis.",
            "habitability_insight": f"A {planet_type.get('type', 'mysterious')} world orbiting {planet_profile.get('host_star')}, currently being audited for biosignatures.",
            "life_probability": "N/A",
            "life_reasoning": "Awaiting baseline characterization of planetary density and composition."
        })


if __name__ == "__main__":
    # Test with sample profile
    test_profile = {
        "name": "TRAPPIST-1 e",
        "host_star": "TRAPPIST-1",
        "star_temp_k": 2566,
        "star_spectral_type": "M8V",
        "radius_earth": 0.92,
        "mass_earth": 0.692,
        "equilibrium_temp_k": 251,
        "orbital_distance_au": 0.02928,
        "orbital_period_days": 6.1,
        "insolation_flux": 0.662,
        "eccentricity": 0.005,
        "distance_ly": 40.7,
        "discovery_method": "Transit",
        "discovery_year": 2017,
        "planet_type": {"type": "Terrestrial", "description": "An Earth-sized rocky world", "icon": "🌍"},
        "habitability": {
            "score": 72,
            "classification": "Promising",
            "habitable_zone": (0.024, 0.049),
            "breakdown": {}
        }
    }
    
    print("Generating bio-report...")
    report = generate_bio_report(test_profile)
    print(json.dumps(report, indent=2))
