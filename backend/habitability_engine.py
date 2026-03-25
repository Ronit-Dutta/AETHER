"""
Habitability Intelligence Engine
Calculates scientific metrics for exoplanet habitability assessment.
Uses astrophysical formulas to determine habitable zones, equilibrium
temperatures, and overall habitability scores.
"""
import math


# Physical constants
STEFAN_BOLTZMANN = 5.670374419e-8  # W⋅m⁻²⋅K⁻⁴
SOLAR_LUMINOSITY = 3.828e26        # Watts
SOLAR_RADIUS = 6.957e8            # meters
SOLAR_TEMP = 5778                  # Kelvin
AU_TO_METERS = 1.496e11           # meters per AU
EARTH_RADIUS = 6.371e6            # meters
EARTH_MASS = 5.972e24             # kg


def calculate_stellar_luminosity(st_teff, st_rad):
    """
    Calculate stellar luminosity from temperature and radius using
    Stefan-Boltzmann Law: L = 4π R² σ T⁴
    
    Args:
        st_teff: Stellar effective temperature (K)
        st_rad: Stellar radius (in solar radii)
    
    Returns:
        Luminosity in solar luminosities, or None if data missing
    """
    if st_teff is None or st_rad is None:
        return None
    
    try:
        radius_m = float(st_rad) * SOLAR_RADIUS
        temp = float(st_teff)
        luminosity_w = 4 * math.pi * radius_m**2 * STEFAN_BOLTZMANN * temp**4
        return luminosity_w / SOLAR_LUMINOSITY
    except (ValueError, TypeError):
        return None


def calculate_habitable_zone(luminosity_solar):
    """
    Calculate the conservative habitable zone boundaries.
    Based on Kopparapu et al. (2013) estimates.
    
    Args:
        luminosity_solar: Stellar luminosity in solar luminosities
    
    Returns:
        Tuple of (inner_hz_au, outer_hz_au) or None
    """
    if luminosity_solar is None or luminosity_solar <= 0:
        return None
    
    try:
        L = float(luminosity_solar)
        # Conservative HZ boundaries (Kopparapu et al. 2013)
        inner_hz = math.sqrt(L / 1.107)  # Runaway greenhouse limit
        outer_hz = math.sqrt(L / 0.356)  # Maximum greenhouse limit
        return (round(inner_hz, 4), round(outer_hz, 4))
    except (ValueError, TypeError):
        return None


def calculate_equilibrium_temperature(st_teff, st_rad, pl_orbsmax, albedo=0.3):
    """
    Calculate planetary equilibrium temperature.
    T_eq = T_star * sqrt(R_star / (2 * a)) * (1 - albedo)^(1/4)
    
    Args:
        st_teff: Stellar effective temperature (K)
        st_rad: Stellar radius (solar radii)
        pl_orbsmax: Orbital semi-major axis (AU)
        albedo: Planetary bond albedo (default 0.3, similar to Earth)
    
    Returns:
        Equilibrium temperature in Kelvin, or None
    """
    if any(v is None for v in [st_teff, st_rad, pl_orbsmax]):
        return None
    
    try:
        t_star = float(st_teff)
        r_star = float(st_rad) * SOLAR_RADIUS
        a = float(pl_orbsmax) * AU_TO_METERS
        
        if a <= 0:
            return None
        
        t_eq = t_star * math.sqrt(r_star / (2 * a)) * (1 - albedo)**0.25
        return round(t_eq, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def classify_planet_type(pl_rade, pl_bmasse):
    """
    Classify a planet based on its radius and mass.
    
    Returns:
        Dictionary with type classification and description
    """
    if pl_rade is None and pl_bmasse is None:
        return {"type": "Unknown", "description": "Insufficient data for classification", "icon": "❓"}
    
    try:
        radius = float(pl_rade) if pl_rade is not None else None
        mass = float(pl_bmasse) if pl_bmasse is not None else None
    except (ValueError, TypeError):
        return {"type": "Unknown", "description": "Invalid data", "icon": "❓"}
    
    # Classification based on radius (in Earth radii)
    if radius is not None:
        if radius < 0.5:
            return {"type": "Sub-Earth", "description": "A small rocky body, likely airless like Mercury or Mars", "icon": "🪨"}
        elif radius < 1.25:
            return {"type": "Terrestrial", "description": "An Earth-sized rocky world, potentially habitable", "icon": "🌍"}
        elif radius < 2.0:
            return {"type": "Super-Earth", "description": "A large rocky world with thick atmosphere, exotic geology possible", "icon": "🌏"}
        elif radius < 4.0:
            return {"type": "Mini-Neptune", "description": "A world with a deep gaseous envelope, possible water layers beneath", "icon": "🔵"}
        elif radius < 10.0:
            return {"type": "Neptune-like", "description": "An ice giant with deep atmosphere of hydrogen, helium, and volatiles", "icon": "💠"}
        elif radius < 25.0:
            return {"type": "Gas Giant", "description": "A massive gas world dominated by hydrogen and helium, like Jupiter", "icon": "🟤"}
        else:
            return {"type": "Super-Jupiter", "description": "An enormous gas planet, potentially a brown dwarf candidate", "icon": "🔴"}
    
    # Fallback to mass classification if radius unavailable
    if mass is not None:
        if mass < 0.5:
            return {"type": "Sub-Earth", "description": "A low-mass rocky body", "icon": "🪨"}
        elif mass < 2.0:
            return {"type": "Terrestrial", "description": "An Earth-mass rocky world", "icon": "🌍"}
        elif mass < 10.0:
            return {"type": "Super-Earth", "description": "A massive rocky world", "icon": "🌏"}
        elif mass < 50.0:
            return {"type": "Neptune-like", "description": "An intermediate-mass volatile-rich world", "icon": "💠"}
        else:
            return {"type": "Gas Giant", "description": "A massive hydrogen-dominated world", "icon": "🟤"}
    
    return {"type": "Unknown", "description": "Insufficient data", "icon": "❓"}


def calculate_habitability_score(planet_data):
    """
    Calculate a comprehensive habitability score (0-100) for an exoplanet.
    Considers: temperature, size, orbital distance, stellar type, and more.
    
    Args:
        planet_data: Dictionary of planet parameters from NASA
    
    Returns:
        Dictionary with score, breakdown, and classification
    """
    score = 0
    breakdown = {}
    max_possible = 0
    
    # --- Factor 1: Equilibrium Temperature (max 30 points) ---
    max_possible += 30
    eq_temp = planet_data.get("pl_eqt")
    if eq_temp is None:
        eq_temp = calculate_equilibrium_temperature(
            planet_data.get("st_teff"),
            planet_data.get("st_rad"),
            planet_data.get("pl_orbsmax")
        )
    
    if eq_temp is not None:
        try:
            t = float(eq_temp)
            # Optimal range: 200K - 330K (liquid water range with margin)
            if 200 <= t <= 330:
                temp_score = 30
            elif 180 <= t < 200 or 330 < t <= 380:
                temp_score = 20
            elif 150 <= t < 180 or 380 < t <= 500:
                temp_score = 10
            elif 100 <= t < 150 or 500 < t <= 700:
                temp_score = 5
            else:
                temp_score = 0
            score += temp_score
            breakdown["temperature"] = {"score": temp_score, "max": 30, "value": f"{t:.0f} K"}
        except (ValueError, TypeError):
            breakdown["temperature"] = {"score": 0, "max": 30, "value": "Unknown"}
    else:
        breakdown["temperature"] = {"score": 0, "max": 30, "value": "Unknown"}
    
    # --- Factor 2: Planet Size (max 25 points) ---
    max_possible += 25
    pl_rade = planet_data.get("pl_rade")
    if pl_rade is not None:
        try:
            r = float(pl_rade)
            if 0.5 <= r <= 1.5:
                size_score = 25  # Earth-like
            elif 1.5 < r <= 2.0:
                size_score = 18  # Super-Earth
            elif 0.3 <= r < 0.5:
                size_score = 12  # Small but possible
            elif 2.0 < r <= 2.5:
                size_score = 8   # Large super-Earth
            else:
                size_score = 2   # Too small or too large
            score += size_score
            breakdown["size"] = {"score": size_score, "max": 25, "value": f"{r:.2f} R⊕"}
        except (ValueError, TypeError):
            breakdown["size"] = {"score": 0, "max": 25, "value": "Unknown"}
    else:
        breakdown["size"] = {"score": 0, "max": 25, "value": "Unknown"}
    
    # --- Factor 3: Habitable Zone Position (max 25 points) ---
    max_possible += 25
    luminosity = planet_data.get("st_lum")
    if luminosity is not None:
        try:
            luminosity = 10 ** float(luminosity)  # NASA stores log10(L/L_sun)
        except (ValueError, TypeError):
            luminosity = calculate_stellar_luminosity(
                planet_data.get("st_teff"), planet_data.get("st_rad")
            )
    else:
        luminosity = calculate_stellar_luminosity(
            planet_data.get("st_teff"), planet_data.get("st_rad")
        )
    
    pl_orbsmax = planet_data.get("pl_orbsmax")
    if luminosity is not None and pl_orbsmax is not None:
        hz = calculate_habitable_zone(luminosity)
        if hz is not None:
            try:
                a = float(pl_orbsmax)
                inner, outer = hz
                mid_hz = (inner + outer) / 2
                hz_width = outer - inner
                
                if inner <= a <= outer:
                    # Within HZ — score based on distance from center
                    dist_from_center = abs(a - mid_hz) / (hz_width / 2)
                    hz_score = int(25 * (1 - dist_from_center * 0.3))
                    hz_score = max(hz_score, 18)
                elif 0.8 * inner <= a < inner or outer < a <= 1.2 * outer:
                    hz_score = 10  # Near HZ
                else:
                    hz_score = 2  # Outside HZ
                score += hz_score
                breakdown["habitable_zone"] = {
                    "score": hz_score, "max": 25,
                    "value": f"{a:.3f} AU (HZ: {inner:.3f}-{outer:.3f} AU)"
                }
            except (ValueError, TypeError):
                breakdown["habitable_zone"] = {"score": 0, "max": 25, "value": "Unknown"}
        else:
            breakdown["habitable_zone"] = {"score": 0, "max": 25, "value": "Unknown"}
    else:
        breakdown["habitable_zone"] = {"score": 0, "max": 25, "value": "Unknown"}
    
    # --- Factor 4: Stellar Properties (max 20 points) ---
    max_possible += 20
    st_teff = planet_data.get("st_teff")
    st_spectype = planet_data.get("st_spectype")
    
    if st_teff is not None:
        try:
            t_star = float(st_teff)
            # G and K type stars are best for habitability
            if 4000 <= t_star <= 6500:
                star_score = 20  # G/K type — ideal
            elif 3500 <= t_star < 4000:
                star_score = 14  # Late K / early M
            elif 6500 < t_star <= 7500:
                star_score = 12  # F type
            elif 3000 <= t_star < 3500:
                star_score = 8   # M-dwarf (tidal locking concerns)
            else:
                star_score = 3   # Too hot or too cool
            score += star_score
            spec = st_spectype if st_spectype else "Unknown"
            breakdown["stellar"] = {"score": star_score, "max": 20, "value": f"{t_star:.0f} K ({spec})"}
        except (ValueError, TypeError):
            breakdown["stellar"] = {"score": 0, "max": 20, "value": "Unknown"}
    else:
        breakdown["stellar"] = {"score": 0, "max": 20, "value": "Unknown"}
    
    # --- Calculate final percentage ---
    percentage = round((score / max_possible) * 100) if max_possible > 0 else 0
    
    # Classification
    if percentage >= 75:
        classification = "Prime Candidate"
        color = "#00ff88"
    elif percentage >= 55:
        classification = "Promising"
        color = "#88ff00"
    elif percentage >= 35:
        classification = "Marginal"
        color = "#ffaa00"
    elif percentage >= 15:
        classification = "Unlikely"
        color = "#ff6600"
    else:
        classification = "Hostile"
        color = "#ff0044"
    
    planet_type = classify_planet_type(
        planet_data.get("pl_rade"),
        planet_data.get("pl_bmasse")
    )
    
    return {
        "score": percentage,
        "raw_score": score,
        "max_score": max_possible,
        "classification": classification,
        "color": color,
        "planet_type": planet_type,
        "breakdown": breakdown,
        "equilibrium_temp": eq_temp,
        "habitable_zone": calculate_habitable_zone(luminosity) if luminosity else None
    }


def generate_planet_profile(planet_data):
    """
    Generate a comprehensive planet profile combining raw NASA data
    with calculated habitability metrics.
    
    Args:
        planet_data: Dictionary from NASA API
    
    Returns:
        Enriched dictionary with all analysis
    """
    hab = calculate_habitability_score(planet_data)
    
    profile = {
        "name": planet_data.get("pl_name", "Unknown"),
        "host_star": planet_data.get("hostname", "Unknown"),
        "discovery_method": planet_data.get("discoverymethod", "Unknown"),
        "discovery_year": planet_data.get("disc_year"),
        "discovery_facility": planet_data.get("disc_facility", "Unknown"),
        "distance_ly": round(float(planet_data["sy_dist"]) * 3.26156, 1) if planet_data.get("sy_dist") else None,
        "distance_pc": planet_data.get("sy_dist"),
        "orbital_period_days": planet_data.get("pl_orbper"),
        "orbital_distance_au": planet_data.get("pl_orbsmax"),
        "radius_earth": planet_data.get("pl_rade"),
        "mass_earth": planet_data.get("pl_bmasse"),
        "equilibrium_temp_k": hab["equilibrium_temp"],
        "insolation_flux": planet_data.get("pl_insol"),
        "eccentricity": planet_data.get("pl_orbeccen"),
        "star_temp_k": planet_data.get("st_teff"),
        "star_radius_solar": planet_data.get("st_rad"),
        "star_mass_solar": planet_data.get("st_mass"),
        "star_spectral_type": planet_data.get("st_spectype"),
        "last_updated": planet_data.get("rowupdate"),
        "habitability": hab,
        "planet_type": hab["planet_type"],
    }
    
    return profile


if __name__ == "__main__":
    # Test with sample data
    test_planet = {
        "pl_name": "Kepler-442 b",
        "hostname": "Kepler-442",
        "discoverymethod": "Transit",
        "disc_year": 2015,
        "pl_orbper": 112.3053,
        "pl_orbsmax": 0.409,
        "pl_rade": 1.34,
        "pl_bmasse": 2.36,
        "pl_eqt": 233,
        "st_teff": 4402,
        "st_rad": 0.598,
        "st_mass": 0.61,
        "st_lum": -0.721,
        "st_spectype": "K",
        "sy_dist": 342.0,
        "discoverymethod": "Transit",
        "disc_facility": "Kepler",
    }
    
    profile = generate_planet_profile(test_planet)
    print(f"🪐 {profile['name']}")
    print(f"   Type: {profile['planet_type']['icon']} {profile['planet_type']['type']}")
    print(f"   Habitability Score: {profile['habitability']['score']}%")
    print(f"   Classification: {profile['habitability']['classification']}")
    print(f"   Breakdown:")
    for key, val in profile['habitability']['breakdown'].items():
        print(f"     {key}: {val['score']}/{val['max']} ({val['value']})")
