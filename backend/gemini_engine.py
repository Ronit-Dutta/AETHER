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
MODEL = "gemini-2.0-flash"


def generate_bio_report(planet_profile):
    """
    Generate a comprehensive speculative evolution bio-report for a planet.
    The AI creates scientifically-grounded hypothetical lifeforms based on
    real planetary parameters.
    
    Args:
        planet_profile: Enriched planet dictionary from habitability_engine
    
    Returns:
        Dictionary containing the bio-report sections
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

    prompt = f"""You are an expert astrobiologist and speculative evolution scientist working for Project AETHER, an autonomous exoplanet mission control system.

Analyze the following REAL NASA data for the exoplanet "{planet_profile['name']}" and generate a scientifically-grounded speculative biology report.

## REAL PLANETARY DATA:
- Planet Name: {planet_profile['name']}
- Host Star: {planet_profile['host_star']}
- Star Temperature: {star_temp} K
- Star Spectral Type: {planet_profile.get('star_spectral_type', 'Unknown')}
- Planet Type: {planet_type.get('type', 'Unknown')} — {planet_type.get('description', '')}
- Radius: {radius} Earth radii
- Mass: {mass} Earth masses
- Equilibrium Temperature: {eq_temp} K ({round(eq_temp - 273.15, 1) if eq_temp else '?'}°C)
- Orbital Distance: {orbital_au} AU
- Orbital Period: {planet_profile.get('orbital_period_days', '?')} days
- Insolation Flux: {insol} Earth flux
- Eccentricity: {planet_profile.get('eccentricity', '?')}
- Distance from Earth: {distance_ly} light-years
- Habitable Zone: {f'{hz[0]}-{hz[1]} AU' if hz else 'Unknown'}
- Habitability Score: {hab.get('score', 0)}% ({hab.get('classification', 'Unknown')})
- Discovery Method: {planet_profile.get('discovery_method', 'Unknown')}
- Discovery Year: {planet_profile.get('discovery_year', 'Unknown')}

## GENERATE THE FOLLOWING SECTIONS (respond in JSON format):

{{
    "environment_summary": "A 2-3 sentence vivid description of what standing on this planet's surface (or in its atmosphere) would be like. Be scientifically grounded but evocative.",
    
    "atmosphere_analysis": "Based on the temperature, mass, and radius, speculate what kind of atmosphere this planet likely has. Mention specific gases and pressures. 2-3 sentences.",
    
    "surface_conditions": "Describe the likely surface: is it rocky, oceanic, icy, gaseous? What would the terrain look like? Consider gravity (based on mass/radius). 2-3 sentences.",
    
    "hypothetical_lifeforms": [
        {{
            "species_name": "A creative scientific-sounding Latin binomial name",
            "common_name": "An evocative common name",
            "description": "2-3 sentences describing this organism's appearance, behavior, and how it survives in this specific environment. Reference the planet's actual conditions.",
            "adaptation": "Key evolutionary adaptation that lets it survive here",
            "size": "Approximate size description",
            "energy_source": "How it gets energy (photosynthesis variant, chemosynthesis, radiation harvesting, etc.)"
        }},
        {{
            "species_name": "Second organism",
            "common_name": "Second common name",
            "description": "2-3 sentences for second organism",
            "adaptation": "Key adaptation",
            "size": "Size",
            "energy_source": "Energy source"
        }},
        {{
            "species_name": "Third organism", 
            "common_name": "Third common name",
            "description": "2-3 sentences for third organism",
            "adaptation": "Key adaptation",
            "size": "Size",
            "energy_source": "Energy source"
        }}
    ],
    
    "habitability_assessment": "A scientific assessment summarizing whether this world could genuinely support life, what type (microbial, complex, intelligent potential), and the key limiting factors. 3-4 sentences.",
    
    "mission_recommendation": "If humanity could send a probe, what should it look for? What instruments would be needed? 2-3 sentences.",
    
    "fun_fact": "One mind-blowing fact about this planet or system derived from the data."
}}

IMPORTANT: 
- Base ALL speculation on the ACTUAL data provided above
- If temperature is extreme, create extremophile organisms
- If the planet is a gas giant, describe aerial lifeforms
- If it's tidally locked, describe organisms adapted to the terminator zone
- Be creative but scientifically plausible
- Return ONLY valid JSON, no markdown formatting"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={
                "temperature": 0.85,
                "max_output_tokens": 3000,
            }
        )
        
        # Parse the JSON response
        text = response.text.strip()
        # Remove any markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        if text.startswith("json"):
            text = text[4:]
        
        bio_report = json.loads(text.strip())
        bio_report["generation_model"] = MODEL
        bio_report["planet_name"] = planet_profile["name"]
        
        print(f"[GEMINI] Bio-report generated for {planet_profile['name']}")
        return bio_report
        
    except json.JSONDecodeError as e:
        print(f"[GEMINI] JSON parse error: {e}")
        print(f"[GEMINI] Raw response: {response.text[:500]}")
        return {
            "error": "Failed to parse AI response",
            "raw_response": response.text[:1000],
            "planet_name": planet_profile["name"]
        }
    except Exception as e:
        print(f"[GEMINI] Error generating bio-report: {e}")
        return {
            "error": str(e),
            "planet_name": planet_profile["name"]
        }


def generate_planet_description(planet_profile):
    """
    Generate a short, compelling description of the planet for the Discovery Card.
    
    Args:
        planet_profile: Enriched planet dictionary
    
    Returns:
        String with a 1-2 sentence compelling description
    """
    hab = planet_profile.get("habitability", {})
    eq_temp = planet_profile.get("equilibrium_temp_k")
    planet_type = planet_profile.get("planet_type", {})

    prompt = f"""You are a science communicator for Project AETHER. Write a single compelling, awe-inspiring sentence (max 30 words) describing the exoplanet {planet_profile['name']}.

Data: Type={planet_type.get('type')}, Temp={eq_temp}K, Radius={planet_profile.get('radius_earth')}x Earth, Score={hab.get('score',0)}%, {hab.get('classification','Unknown')}.

Return ONLY the sentence, no quotes or formatting."""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={
                "temperature": 0.9,
                "max_output_tokens": 100,
            }
        )
        return response.text.strip()
    except Exception as e:
        print(f"[GEMINI] Error generating description: {e}")
        return f"A {planet_type.get('type', 'mysterious')} world awaiting further analysis."


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
