import math
import numpy as np

def calculate_initial_dose_rate(yield_kt):

    if yield_kt <= 0:
        return 0.0

    base_rate = 100  

    initial_dose_rate = base_rate * (yield_kt / 15.0) ** 0.8

    return initial_dose_rate

def calculate_blast_radii(yield_kt):

    if yield_kt <= 0:
        return {}

    Y_MT = yield_kt / 1000.0  

    radii = {}

    radii['fireball_km'] = 0.09 * (Y_MT ** 0.4)

    radii['burns_3rd_degree_km'] = 0.8 * (Y_MT ** 0.41)

    radii['blast_20_psi_km'] = 0.28 * (Y_MT ** 0.33)  

    radii['blast_5_psi_km'] = 0.54 * (Y_MT ** 0.40)   

    radii['blast_2_psi_km'] = 0.91 * (Y_MT ** 0.33)   

    radii['radiation_500_rem_km'] = 0.65 * (Y_MT ** 0.19)  

    radii['radiation_100_rem_km'] = 1.15 * (Y_MT ** 0.19)  

    radii['emp_km'] = 2.4 * (Y_MT ** 0.25)

    return radii

def calculate_crater_dimensions(yield_kt, burst_type='surface'):

    if yield_kt <= 0:
        return {}

    Y_MT = yield_kt / 1000.0

    crater = {}

    if burst_type == 'surface':

        crater['diameter_m'] = 140 * (Y_MT ** 0.3)
        crater['depth_m'] = 24 * (Y_MT ** 0.3)
    else:  # subsurface

        crater['diameter_m'] = 120 * (Y_MT ** 0.25)
        crater['depth_m'] = 35 * (Y_MT ** 0.3)

    crater['radius_m'] = crater['diameter_m'] / 2
    crater['volume_m3'] = (math.pi / 3) * (crater['radius_m'] ** 2) * crater['depth_m']

    return crater

def estimate_casualties(yield_kt, population_density=1000):

    if yield_kt <= 0:
        return {}

    radii = calculate_blast_radii(yield_kt)

    casualties = {}

    area_20_psi = math.pi * (radii['blast_20_psi_km'] ** 2)
    area_5_psi = math.pi * (radii['blast_5_psi_km'] ** 2)
    area_2_psi = math.pi * (radii['blast_2_psi_km'] ** 2)

    casualties['severe_zone_km2'] = area_20_psi
    casualties['moderate_zone_km2'] = area_5_psi - area_20_psi
    casualties['light_zone_km2'] = area_2_psi - area_5_psi

    casualties['severe_pop'] = int(area_20_psi * population_density)
    casualties['moderate_pop'] = int((area_5_psi - area_20_psi) * population_density)
    casualties['light_pop'] = int((area_2_psi - area_5_psi) * population_density)

    casualties['estimated_fatalities'] = int(
        casualties['severe_pop'] * 0.90 +      

        casualties['moderate_pop'] * 0.50 +    

        casualties['light_pop'] * 0.05         

    )

    casualties['estimated_injuries'] = int(
        casualties['severe_pop'] * 0.09 +      

        casualties['moderate_pop'] * 0.40 +    

        casualties['light_pop'] * 0.25         

    )

    casualties['total_affected'] = (casualties['severe_pop'] + 
                                   casualties['moderate_pop'] + 
                                   casualties['light_pop'])

    return casualties

def calculate_mushroom_cloud_height(yield_kt):

    if yield_kt <= 0:
        return {}

    Y_MT = yield_kt / 1000.0

    cloud = {}

    cloud['height_km'] = 12.0 * (Y_MT ** 0.2)  

    cloud['height_m'] = cloud['height_km'] * 1000

    cloud['width_km'] = 2.0 * (Y_MT ** 0.25)
    cloud['width_m'] = cloud['width_km'] * 1000

    cloud['stem_height_km'] = 0.3 * cloud['height_km']
    cloud['stem_height_m'] = cloud['stem_height_km'] * 1000

    return cloud

def estimate_emp_effects(yield_kt, burst_altitude_km=0):

    if yield_kt <= 0:
        return {}

    Y_MT = yield_kt / 1000.0

    emp = {}

    if burst_altitude_km < 30:  

        emp['affected_radius_km'] = 2.4 * (Y_MT ** 0.25)
        emp['peak_field_strength'] = 50000 * (Y_MT ** 0.5)  

        emp['emp_type'] = 'Local'

    elif burst_altitude_km < 100:  

        emp['affected_radius_km'] = 50 * (Y_MT ** 0.3)
        emp['peak_field_strength'] = 25000 * (Y_MT ** 0.4)
        emp['emp_type'] = 'Regional'

    else:  # Very high altitude (HEMP)

        emp['affected_radius_km'] = 1000 * (Y_MT ** 0.2)
        emp['peak_field_strength'] = 10000 * (Y_MT ** 0.3)
        emp['emp_type'] = 'Continental'

    emp['burst_altitude_km'] = burst_altitude_km
    emp['electronics_damage_radius_km'] = emp['affected_radius_km'] * 0.7
    emp['power_grid_damage_radius_km'] = emp['affected_radius_km'] * 0.9

    return emp

def calculate_comprehensive_effects(yield_kt, burst_altitude_km=0, population_density=1000):

    if yield_kt <= 0:
        return {}

    effects = {
        'weapon_yield_kt': yield_kt,
        'burst_altitude_km': burst_altitude_km,
        'burst_type': 'surface' if burst_altitude_km == 0 else 'airburst',
    }

    effects['blast_radii'] = calculate_blast_radii(yield_kt)
    effects['casualties'] = estimate_casualties(yield_kt, population_density)
    effects['mushroom_cloud'] = calculate_mushroom_cloud_height(yield_kt)
    effects['emp_effects'] = estimate_emp_effects(yield_kt, burst_altitude_km)

    if burst_altitude_km == 0:
        effects['crater'] = calculate_crater_dimensions(yield_kt, 'surface')

    if 'blast_5_psi_km' in effects['blast_radii']:
        destruction_radius = effects['blast_radii']['blast_5_psi_km']
        effects['total_destruction_area_km2'] = math.pi * (destruction_radius ** 2)

    return effects

def create_effects_summary(yield_kt, burst_altitude_km=0, population_density=1000):

    effects = calculate_comprehensive_effects(yield_kt, burst_altitude_km, population_density)

    if not effects:
        return "No effects data available."

    summary = f"NUCLEAR WEAPON EFFECTS ANALYSIS\n"
    summary += f"{'='*40}\n\n"

    summary += f"Weapon Yield: {yield_kt:,.0f} kilotons\n"
    summary += f"Burst Type: {effects['burst_type'].title()}\n"
    if burst_altitude_km > 0:
        summary += f"Burst Altitude: {burst_altitude_km:.1f} km\n"
    summary += f"Population Density: {population_density:,} people/km²\n\n"

    if 'blast_radii' in effects:
        blast = effects['blast_radii']
        summary += f"BLAST EFFECTS:\n"
        summary += f"  Complete destruction (20 psi): {blast.get('blast_20_psi_km', 0):.2f} km radius\n"
        summary += f"  Heavy damage (5 psi): {blast.get('blast_5_psi_km', 0):.2f} km radius\n"
        summary += f"  Moderate damage (2 psi): {blast.get('blast_2_psi_km', 0):.2f} km radius\n\n"

    if 'blast_radii' in effects and 'burns_3rd_degree_km' in effects['blast_radii']:
        thermal = effects['blast_radii']['burns_3rd_degree_km']
        summary += f"THERMAL EFFECTS:\n"
        summary += f"  3rd degree burns: {thermal:.2f} km radius\n\n"

    if 'blast_radii' in effects:
        blast = effects['blast_radii']
        if 'radiation_500_rem_km' in blast:
            summary += f"PROMPT RADIATION:\n"
            summary += f"  Lethal dose (500 rem): {blast['radiation_500_rem_km']:.2f} km radius\n"
            summary += f"  Severe effects (100 rem): {blast['radiation_100_rem_km']:.2f} km radius\n\n"

    if 'casualties' in effects:
        cas = effects['casualties']
        summary += f"CASUALTY ESTIMATES:\n"
        summary += f"  Total affected population: {cas.get('total_affected', 0):,}\n"
        summary += f"  Estimated fatalities: {cas.get('estimated_fatalities', 0):,}\n"
        summary += f"  Estimated injuries: {cas.get('estimated_injuries', 0):,}\n\n"

    if 'mushroom_cloud' in effects:
        cloud = effects['mushroom_cloud']
        summary += f"MUSHROOM CLOUD:\n"
        summary += f"  Maximum height: {cloud.get('height_km', 0):.1f} km\n"
        summary += f"  Cloud width: {cloud.get('width_km', 0):.1f} km\n\n"

    if 'emp_effects' in effects:
        emp = effects['emp_effects']
        summary += f"EMP EFFECTS:\n"
        summary += f"  Type: {emp.get('emp_type', 'Unknown')}\n"
        summary += f"  Affected radius: {emp.get('affected_radius_km', 0):.1f} km\n"
        summary += f"  Electronics damage: {emp.get('electronics_damage_radius_km', 0):.1f} km\n\n"

    if 'crater' in effects:
        crater = effects['crater']
        summary += f"CRATER:\n"
        summary += f"  Diameter: {crater.get('diameter_m', 0):.0f} meters\n"
        summary += f"  Depth: {crater.get('depth_m', 0):.0f} meters\n\n"

    if 'total_destruction_area_km2' in effects:
        area = effects['total_destruction_area_km2']
        summary += f"TOTAL DESTRUCTION AREA: {area:.1f} km²\n"

    return summary

def test_fallout_calculator():
    """Test the enhanced fallout calculator functions."""
    print("Testing Enhanced Fallout Calculator...")
    print("=" * 45)

    test_yields = [15, 150, 1000]  

    for yield_kt in test_yields:
        print(f"\n--- Testing {yield_kt} kt weapon ---")

        print('testing values- 1')

        radii = calculate_blast_radii(yield_kt)
        print(f"Blast radius (5 psi): {radii.get('blast_5_psi_km', 0):.2f} km")
        print(f"Thermal burns: {radii.get('burns_3rd_degree_km', 0):.2f} km")

        cloud = calculate_mushroom_cloud_height(yield_kt)
        print(f"Cloud height: {cloud.get('height_km', 0):.1f} km")

        casualties = estimate_casualties(yield_kt, 3000)  

        print(f"Est. fatalities: {casualties.get('estimated_fatalities', 0):,}")

    print(f"\n--- Comprehensive Effects Example ---")
    summary = create_effects_summary(150, 0, 2000)  

    print(summary)

if __name__ == "__main__":
    test_fallout_calculator()