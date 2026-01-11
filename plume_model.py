import math
import numpy as np

def calculate_casualties(yield_kt, population_density=25000):
    """
    Enhanced casualty calculation based on NUKEMAP methodology with more realistic scaling.
    This accounts for both prompt effects and secondary effects with improved accuracy.

    Args:
        yield_kt: Weapon yield in kilotons
        population_density: People per square km (adjusted for Delhi's actual density)

    Returns:
        dict: Casualty estimates with detailed breakdown
    """
    if yield_kt <= 0:
        return {"fatalities": 0, "injuries": 0}

    print(f"Calculating casualties for {yield_kt}kt weapon, density {population_density}/km²")

    effective_density = population_density * 1.5  

    Y_MT = yield_kt / 1000.0  

    fireball_radius = 0.44 * (Y_MT ** 0.4)
    psi_20_radius = 1.3 * (Y_MT ** 0.33)     

    psi_5_radius = 4.5 * (Y_MT ** 0.33)     

    psi_2_radius = 8.0 * (Y_MT ** 0.33)     

    psi_1_radius = 13.0 * (Y_MT ** 0.33)    
# Light damage

    thermal_radius = 0.9 * (Y_MT ** 0.41)

    radiation_radius = 0.65 * (Y_MT ** 0.19)

    print(f"Blast radii: 20psi={psi_20_radius:.2f}km, 5psi={psi_5_radius:.2f}km, 2psi={psi_2_radius:.2f}km")

    area_fireball = math.pi * (fireball_radius ** 2)
    area_20_psi = math.pi * (psi_20_radius ** 2) - area_fireball
    area_5_psi = math.pi * (psi_5_radius ** 2) - math.pi * (psi_20_radius ** 2)
    area_2_psi = math.pi * (psi_2_radius ** 2) - math.pi * (psi_5_radius ** 2)
    area_1_psi = math.pi * (psi_1_radius ** 2) - math.pi * (psi_2_radius ** 2)
    area_thermal = math.pi * (thermal_radius ** 2)
    area_radiation = math.pi * (radiation_radius ** 2)

    print(f"Areas: fireball={area_fireball:.2f}km², 20psi={area_20_psi:.2f}km², 5psi={area_5_psi:.2f}km²")

    pop_fireball = area_fireball * effective_density
    pop_20_psi = area_20_psi * effective_density
    pop_5_psi = area_5_psi * effective_density
    pop_2_psi = area_2_psi * effective_density
    pop_1_psi = area_1_psi * effective_density

    print(f"Populations: fireball={pop_fireball:.0f}, 20psi={pop_20_psi:.0f}, 5psi={pop_5_psi:.0f}")

    fatalities_fireball = pop_fireball * 1.0
    injuries_fireball = 0  

    fatalities_20_psi = pop_20_psi * 0.98
    injuries_20_psi = pop_20_psi * 0.02

    fatalities_5_psi = pop_5_psi * 0.65
    injuries_5_psi = pop_5_psi * 0.30

    fatalities_2_psi = pop_2_psi * 0.15
    injuries_2_psi = pop_2_psi * 0.60

    fatalities_1_psi = pop_1_psi * 0.03
    injuries_1_psi = pop_1_psi * 0.45

    thermal_only_area = max(0, area_thermal - math.pi * (psi_1_radius ** 2))
    thermal_only_pop = thermal_only_area * effective_density

    thermal_fatalities = thermal_only_pop * 0.40  

    thermal_injuries = thermal_only_pop * 0.55    

    radiation_only_area = max(0, area_radiation - math.pi * (psi_1_radius ** 2))
    radiation_only_pop = radiation_only_area * effective_density

    radiation_fatalities = radiation_only_pop * 0.45  

    radiation_injuries = radiation_only_pop * 0.40    

    total_blast_fatalities = (fatalities_fireball + fatalities_20_psi + 
                             fatalities_5_psi + fatalities_2_psi + fatalities_1_psi)

    total_blast_injuries = (injuries_fireball + injuries_20_psi + 
                           injuries_5_psi + injuries_2_psi + injuries_1_psi)

    final_fatalities = int(total_blast_fatalities + thermal_fatalities + radiation_fatalities)
    final_injuries = int(total_blast_injuries + thermal_injuries + radiation_injuries)

    total_affected = int(pop_fireball + pop_20_psi + pop_5_psi + pop_2_psi + pop_1_psi + 
                        thermal_only_pop + radiation_only_pop)

    print(f"Final casualties: {final_fatalities:,} fatalities, {final_injuries:,} injuries")

    return {
        "fatalities": final_fatalities,
        "injuries": final_injuries,
        "total_affected": total_affected,
        "blast_radii": {
            "fireball_km": round(fireball_radius, 2),
            "psi_20_km": round(psi_20_radius, 2),
            "psi_5_km": round(psi_5_radius, 2),
            "psi_2_km": round(psi_2_radius, 2),
            "psi_1_km": round(psi_1_radius, 2),
            "thermal_km": round(thermal_radius, 2),
            "radiation_km": round(radiation_radius, 2)
        },
        "casualties_by_zone": {
            "fireball": {"fatalities": int(fatalities_fireball), "injuries": int(injuries_fireball)},
            "psi_20": {"fatalities": int(fatalities_20_psi), "injuries": int(injuries_20_psi)},
            "psi_5": {"fatalities": int(fatalities_5_psi), "injuries": int(injuries_5_psi)},
            "psi_2": {"fatalities": int(fatalities_2_psi), "injuries": int(injuries_2_psi)},
            "psi_1": {"fatalities": int(fatalities_1_psi), "injuries": int(injuries_1_psi)},
            "thermal_only": {"fatalities": int(thermal_fatalities), "injuries": int(thermal_injuries)},
            "radiation_only": {"fatalities": int(radiation_fatalities), "injuries": int(radiation_injuries)}
        }
    }

DELHI_POPULATION_DENSITIES = {
    'Rural (1,000/km²)': 1000,
    'Suburban (5,000/km²)': 5000,
    'Urban (15,000/km²)': 15000,
    'Dense Urban (35,000/km²)': 35000,
    'Very Dense Urban (60,000/km²)': 60000,
    'Central Delhi (80,000/km²)': 80000,
    'Custom': 0
}

def test_casualty_calculations():
    """Test casualty calculations against NUKEMAP values"""
    print("TESTING IMPROVED CASUALTY CALCULATIONS")
    print("=" * 50)

    test_cases = [
        {
            "name": "10kt weapon on Delhi (NUKEMAP comparison)",
            "yield": 10,
            "density": 35000,  

            "nukemap_fatalities": 134330,  

            "nukemap_injuries": 541510
        },
        {
            "name": "100kt weapon on Delhi (NUKEMAP comparison)",
            "yield": 100,
            "density": 35000,  

            "nukemap_fatalities": 614290,  

            "nukemap_injuries": 2140370
        },
        {
            "name": "15kt Hiroshima-scale on Delhi",
            "yield": 15,
            "density": 40000,  

            "nukemap_fatalities": 200000,  

            "nukemap_injuries": 600000
        }
    ]

    for case in test_cases:
        print(f"\n--- {case['name']} ---")
        result = calculate_casualties(case["yield"], case["density"])

        fatalities = result["fatalities"]
        injuries = result["injuries"]

        print(f"Population density: {case['density']:,}/km²")
        print(f"Calculated fatalities: {fatalities:,}")
        print(f"NUKEMAP fatalities: {case['nukemap_fatalities']:,}")
        print(f"Calculated injuries: {injuries:,}")
        print(f"NUKEMAP injuries: {case['nukemap_injuries']:,}")

        fat_diff = abs(fatalities - case['nukemap_fatalities']) / case['nukemap_fatalities'] * 100
        inj_diff = abs(injuries - case['nukemap_injuries']) / case['nukemap_injuries'] * 100

        print(f"Fatality difference: {fat_diff:.1f}%")
        print(f"Injury difference: {inj_diff:.1f}%")

        radii = result["blast_radii"]
        print(f"Key blast radii: 5psi={radii['psi_5_km']:.2f}km, 2psi={radii['psi_2_km']:.2f}km, 1psi={radii['psi_1_km']:.2f}km")

if __name__ == "__main__":
    test_casualty_calculations()