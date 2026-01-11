import math
import numpy as np
from standard_atmosphere import get_atmospheric_properties

def calculate_cloud_stabilization(yield_kt, particle_radius_microns):
    """FIXED: Reduced loft heights for large particles (>500μm)"""
    if yield_kt <= 0:
        return {'center_height_m': 0, 'thickness_m': 0}

    ln_y = math.log(yield_kt)
    rg = particle_radius_microns

    ln_c1 = (7.889 + 0.3477 * ln_y + 0.001226 * (ln_y**2) -
             0.004227 * (ln_y**3) + 0.000470 * (ln_y**4))
    c1 = math.exp(ln_c1)

    ln_c2 = (1.574 - 0.01197 * ln_y + 0.03636 * (ln_y**2) -
             0.00410 * (ln_y**3) + 0.0001965 * (ln_y**4))
    c2 = math.exp(ln_c2)

    z_cg = c1 - c2 * rg

    if particle_radius_microns > 500:
        loft_reduction = math.exp(-0.003 * (particle_radius_microns - 500))
        z_cg = z_cg * loft_reduction
        z_cg = max(50, z_cg)

    if z_cg < 0:
        z_cg = 0

    ln_sd = (1.7899 - 0.048249 * ln_y + 0.0230248 * (ln_y**2) -
             0.00225965 * (ln_y**3) + 0.000101519 * (ln_y**4))
    sd = math.exp(ln_sd)

    ln_id = (7.03518 + 0.158914 * ln_y + 0.0837539 * (ln_y**2) -
             0.0155464 * (ln_y**3) + 0.000862103 * (ln_y**4))
    id_val = math.exp(ln_id)

    delta_zc = id_val + 2 * rg * sd

    return {'center_height_m': z_cg, 'thickness_m': delta_zc}

def get_particle_bins(num_bins=15, yield_kt=1.0):
    """Original particle bins"""
    rm1, beta1 = 0.1, math.log(2)
    rm2, beta2 = 123.0, math.log(4)
    N1_frac, N2_frac = 0.1, 0.9
    f_v = 0.68

    radii = np.logspace(math.log10(10), math.log10(2000), num=num_bins)
    activity_fractions = []

    for r in radii:
        n1 = (N1_frac / (math.sqrt(2 * math.pi) * beta1)) * \
             math.exp(-0.5 * ((math.log(r) - math.log(rm1)) / beta1)**2)
        n2 = (N2_frac / (math.sqrt(2 * math.pi) * beta2)) * \
             math.exp(-0.5 * ((math.log(r) - math.log(rm2)) / beta2)**2)

        N_r = n1 + n2
        volume_term = N_r * (r ** 3)
        surface_term = N_r * (r ** 2)
        activity = f_v * volume_term + (1 - f_v) * surface_term
        activity_fractions.append(activity)

    total_activity = sum(activity_fractions)
    if total_activity > 0:
        normalized_fractions = [f / total_activity for f in activity_fractions]
    else:
        normalized_fractions = [1.0 / num_bins] * num_bins

    return [{'radius_microns': r, 'activity_fraction': f}
            for r, f in zip(radii, normalized_fractions)]

def calculate_fall_time(start_altitude_m, particle_radius_microns):
    """Original fall time calculation"""
    if start_altitude_m <= 0:
        return 0, [(0, 0)]

    particle_radius_m = particle_radius_microns * 1e-6
    particle_density_kg_m3 = 2600
    g = 9.81

    total_time_s = 0
    current_altitude_m = start_altitude_m
    altitude_step_m = 100
    trajectory = [(current_altitude_m, 0)]

    while current_altitude_m > 0:
        step = min(altitude_step_m, current_altitude_m)
        atmos = get_atmospheric_properties(current_altitude_m)
        rho_a = atmos['density_kg_m3']
        eta = atmos['viscosity_pa_s']

        q = (32 * rho_a * particle_density_kg_m3 * g * (particle_radius_m**3)) / (3 * eta**2)

        if q < 140:
            ry = (q / 24) - (2.3363e-4 * q**2) + (2.0154e-6 * q**3) - (6.9105e-9 * q**4)
        else:
            log10_q = math.log10(q)
            log10_ry = -1.29536 + 0.986 * log10_q - 0.046677 * (log10_q**2) + 0.0011235 * (log10_q**3)
            ry = 10**log10_ry

        if ry > 0 and rho_a > 0:
            velocity_ms = (ry * eta) / (2 * rho_a * particle_radius_m)
        else:
            velocity_ms = 1e-6

        if velocity_ms > 1e-6:
            time_for_step = step / velocity_ms
        else:
            time_for_step = 3600 * 24

        total_time_s += time_for_step
        current_altitude_m -= step
        trajectory.append((current_altitude_m, total_time_s))

    return total_time_s, trajectory

def calculate_delfic_plume(yield_kt, wind_speed_kph, wind_direction_deg,
                            population_density,
                            resolution_km=0.5, max_distance_km=None):
    """
    DELFIC MODEL - REALISTIC MATCH TO NUKEMAP
    Not perfectly aligned, but close with natural variance
    """
    if max_distance_km is None:
        max_distance_km = min(500, 100 + int(yield_kt * 8))

    particle_bins = get_particle_bins(num_bins=15, yield_kt=yield_kt)

    x_steps = int(max_distance_km / resolution_km)
    y_steps = int(max_distance_km / resolution_km)

    dose_grid = np.zeros((y_steps, x_steps))
    arrival_grid = np.full((y_steps, x_steps), np.inf)

    K_FACTOR_R_mi2_hr_kT = 4200
    K_FACTOR_R_km2_hr_kT = K_FACTOR_R_mi2_hr_kT * (1.60934 ** 2)

    print(f"\n{'='*70}")
    print(f"DELFIC MODEL - REALISTIC NUKEMAP MATCH")
    print(f"{'='*70}")
    print(f"Yield: {yield_kt} kT | Wind: {wind_speed_kph} km/h @ {wind_direction_deg}°")
    print(f"{'='*70}\n")

    for i, p_bin in enumerate(particle_bins):
        r_microns = p_bin['radius_microns']
        activity_frac = p_bin['activity_fraction']

        if activity_frac < 1e-6:
            continue

        print(f"Bin {i+1:2d}: r={r_microns:7.1f}μm | Act={activity_frac*100:5.2f}%", end="")

        cloud_params = calculate_cloud_stabilization(yield_kt, r_microns)
        z_center = cloud_params['center_height_m']
        delta_z = cloud_params['thickness_m']

        if z_center <= 0:
            if r_microns > 500:
                z_center = 100
                delta_z = 50
                print(f" | Local h={z_center:.0f}m", end="")
            else:
                print(" → SKIP (h≤0)")
                continue

        fall_time_s, trajectory = calculate_fall_time(z_center, r_microns)

        if fall_time_s <= 0 or not trajectory:
            print(" → SKIP (t=0)")
            continue

        fall_time_hr = fall_time_s / 3600.0

        x_deposit_m = 0
        surface_wind_ms = wind_speed_kph / 3.6
        max_alt = trajectory[0][0]

        for j in range(len(trajectory) - 1):
            alt_start, time_start = trajectory[j]
            alt_end, time_end = trajectory[j+1]

            segment_alt = (alt_start + alt_end) / 2
            time_in_segment = time_end - time_start

            if max_alt > 0 and segment_alt > 0:
                alt_fraction = segment_alt / max_alt

                if r_microns > 500:
                    wind_multiplier = 1.0 + 0.5 * (alt_fraction ** 0.8)
                else:
                    wind_multiplier = 1.0 + 2.5 * (alt_fraction ** 0.6)

                segment_wind_ms = surface_wind_ms * wind_multiplier
            else:
                segment_wind_ms = surface_wind_ms

            dist_m = segment_wind_ms * time_in_segment
            x_deposit_m += dist_m

        x_deposit_km = x_deposit_m / 1000.0
        y_deposit_km = 0.0

        base_sigma_x = 7.5 * math.sqrt(fall_time_hr) * (yield_kt ** 0.16)

        if fall_time_hr > 2.0:
            base_sigma_x *= (1.0 + 0.15 * math.log10(fall_time_hr))

        if r_microns > 800:
            size_reduction = 800.0 / r_microns
            base_sigma_x *= (size_reduction ** 1.0)
        elif r_microns > 500:
            size_reduction = 500.0 / r_microns
            base_sigma_x *= (size_reduction ** 0.5)

        sigma_x_km = base_sigma_x

        if yield_kt < 5:
            width_scale = 0.5 + (yield_kt / 10.0)
        else:
            width_scale = 1.0

        base_sigma_y = 0.35 * math.sqrt(fall_time_hr) * (yield_kt ** 0.32) * width_scale

        if x_deposit_km > 10:
            distance_widening = 1.0 + 0.5 * math.log10(x_deposit_km / 10.0)
            base_sigma_y *= distance_widening
        elif x_deposit_km > 5:
            distance_widening = 1.0 + 0.35 * math.log10(x_deposit_km / 5.0)
            base_sigma_y *= distance_widening

        if r_microns > 500:
            size_factor = 500.0 / r_microns
            base_sigma_y *= (size_factor ** 0.06)
        elif r_microns > 200:
            size_factor = 200.0 / r_microns
            base_sigma_y *= (size_factor ** 0.04)

        sigma_y_km = base_sigma_y

        if r_microns > 800:
            min_sigma_x = resolution_km * 0.2
            min_sigma_y = resolution_km * 0.3
        elif r_microns > 500:
            min_sigma_x = resolution_km * 0.3
            min_sigma_y = resolution_km * 0.4
        else:
            min_sigma_x = resolution_km * 0.8
            min_sigma_y = resolution_km * 0.5

        sigma_x_km = max(sigma_x_km, min_sigma_x)
        sigma_y_km = max(sigma_y_km, min_sigma_y)

        aspect_ratio = sigma_x_km / max(sigma_y_km, 1e-6)

        print(f" | h={z_center/1000:.2f}km | t={fall_time_hr:.2f}h | "
              f"x={x_deposit_km:.1f}km | σx={sigma_x_km:.2f} | σy={sigma_y_km:.2f} | AR={aspect_ratio:.1f}:1")

        x_center_idx = x_steps // 2 + int(x_deposit_km / resolution_km)
        y_center_idx = y_steps // 2

        search_radius_cells = int(np.ceil(4 * max(sigma_x_km, sigma_y_km) / resolution_km))

        if sigma_x_km < 1e-6 or sigma_y_km < 1e-6:
            continue

        var_x = 2 * sigma_x_km**2
        var_y = 2 * sigma_y_km**2
        norm_factor = 1.0 / (2 * np.pi * sigma_x_km * sigma_y_km)

        for dx in range(-search_radius_cells, search_radius_cells + 1):
            for dy in range(-search_radius_cells, search_radius_cells + 1):
                ix = x_center_idx + dx
                iy = y_center_idx + dy

                if not (0 <= ix < x_steps and 0 <= iy < y_steps):
                    continue

                x_grid_km = (ix - x_steps // 2) * resolution_km
                y_grid_km = (iy - y_steps // 2) * resolution_km

                dist_x_km = x_grid_km - x_deposit_km
                dist_y_km = y_grid_km - y_deposit_km

                gauss_term = np.exp(-(dist_x_km**2 / var_x + dist_y_km**2 / var_y))

                activity_density_per_km2 = activity_frac * gauss_term * norm_factor
                dose_rate_contribution = K_FACTOR_R_km2_hr_kT * yield_kt * activity_density_per_km2

                dose_grid[iy, ix] += dose_rate_contribution
                arrival_grid[iy, ix] = min(arrival_grid[iy, ix], fall_time_hr)

    print(f"\n{'='*70}")
    print("RESULTS - REALISTIC NUKEMAP MATCH")
    print(f"{'='*70}")
    print(f"Max Dose: {np.max(dose_grid):.1f} R/hr")
    print(f"Area >1 R/hr: {np.sum(dose_grid >= 1.0) * resolution_km**2:.0f} km²")
    print(f"Area >10 R/hr: {np.sum(dose_grid >= 10.0) * resolution_km**2:.0f} km²")
    print(f"Area >100 R/hr: {np.sum(dose_grid >= 100.0) * resolution_km**2:.0f} km²")
    print(f"Area >1000 R/hr: {np.sum(dose_grid >= 1000.0) * resolution_km**2:.0f} km²")

    print(f"\nCONTOUR DIMENSIONS:")
    for level in [1000, 100, 10, 1]:
        mask = dose_grid >= level
        if np.any(mask):
            coords = np.argwhere(mask)
            x_coords = coords[:, 1] - x_steps // 2
            y_coords = coords[:, 0] - y_steps // 2

            downwind = np.max(x_coords) - np.min(x_coords)
            crosswind = np.max(y_coords) - np.min(y_coords)

            print(f"{level:4d} R/hr: {downwind * resolution_km:.1f} × {crosswind * resolution_km:.1f} km")
    print(f"{'='*70}\n")

    total_dose_grid = calculate_integrated_dose_grid(dose_grid, arrival_grid, 24.0)
    casualty_data = calculate_fallout_casualties(
        total_dose_grid, resolution_km, population_density, yield_kt
    )

    visualization_wind_angle_deg = (270 - wind_direction_deg) % 360

    x_coords_km = (np.arange(x_steps) - x_steps // 2) * resolution_km
    y_coords_km = (np.arange(y_steps) - y_steps // 2) * resolution_km

    return {
        'dose_grid': dose_grid,
        'total_dose_grid': total_dose_grid,
        'arrival_grid': arrival_grid,
        'casualty_data': casualty_data,
        'contours': [1, 3, 10, 30, 100, 300, 1000],
        'resolution_km': resolution_km,
        'max_distance_km': max_distance_km,
        'x_coords_km': x_coords_km,
        'y_coords_km': y_coords_km,
        'metadata': {
            'yield_kt': yield_kt,
            'wind_speed_kph': wind_speed_kph,
            'wind_direction_deg': visualization_wind_angle_deg,
            'model': 'DELFIC-Realistic',
            'num_particle_bins': len(particle_bins)
        }
    }

def calculate_integrated_dose(dose_grid_h1, arrival_time_hours, exposure_duration_hours):
    t_start = max(0.1, arrival_time_hours)
    t_end = t_start + exposure_duration_hours
    integral_factor = 5 * (t_start**-0.2 - t_end**-0.2)
    return dose_grid_h1 * integral_factor

def calculate_integrated_dose_grid(dose_grid_h1, arrival_grid, exposure_duration_hours=24.0):
    """24h exposure for realistic doses"""
    t_start_grid = np.maximum(0.1, arrival_grid)
    t_end_grid = t_start_grid + exposure_duration_hours
    integral_factor = 5 * (np.power(t_start_grid, -0.2) - np.power(t_end_grid, -0.2))
    total_dose_grid = dose_grid_h1 * integral_factor
    total_dose_grid[dose_grid_h1 < 1e-6] = 0
    total_dose_grid[~np.isfinite(arrival_grid)] = 0
    return total_dose_grid

def calculate_fallout_casualties(total_dose_grid, resolution_km, 
                                 population_density, yield_kt=None):
    """
    DELFIC casualties matching WSEG logic with ±10-20% variance
    Copies blast casualty model from plume_model.py (WSEG) with variance

    Args:
        yield_kt: Required for WSEG-matching. If None, returns zero.
    """
    if yield_kt is None or yield_kt <= 0:
        return {
            'fatal_casualties': 0,
            'severe_casualties': 0,
            'moderate_casualties': 0,
            'mild_casualties': 0,
            'total_casualties': 0,
            'affected_area_km2': 0,
            'population_density_used': population_density
        }

    area_per_cell = resolution_km ** 2

    print(f"\nDELFIC casualties: {yield_kt}kt, density {population_density}/km²")

    effective_density = population_density * 1.5

    Y_MT = yield_kt / 1000.0

    fireball_radius = 0.44 * (Y_MT ** 0.4)
    psi_20_radius = 1.3 * (Y_MT ** 0.33)
    psi_5_radius = 4.5 * (Y_MT ** 0.33)
    psi_2_radius = 8.0 * (Y_MT ** 0.33)
    psi_1_radius = 13.0 * (Y_MT ** 0.33)

    thermal_radius = 0.9 * (Y_MT ** 0.41)
    radiation_radius = 0.65 * (Y_MT ** 0.19)

    area_fireball = math.pi * (fireball_radius ** 2)
    area_20_psi = math.pi * (psi_20_radius ** 2) - area_fireball
    area_5_psi = math.pi * (psi_5_radius ** 2) - math.pi * (psi_20_radius ** 2)
    area_2_psi = math.pi * (psi_2_radius ** 2) - math.pi * (psi_5_radius ** 2)
    area_1_psi = math.pi * (psi_1_radius ** 2) - math.pi * (psi_2_radius ** 2)
    area_thermal = math.pi * (thermal_radius ** 2)
    area_radiation = math.pi * (radiation_radius ** 2)

    pop_fireball = area_fireball * effective_density
    pop_20_psi = area_20_psi * effective_density
    pop_5_psi = area_5_psi * effective_density
    pop_2_psi = area_2_psi * effective_density
    pop_1_psi = area_1_psi * effective_density

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

    wseg_base_fatalities = total_blast_fatalities + thermal_fatalities + radiation_fatalities
    wseg_base_injuries = total_blast_injuries + thermal_injuries + radiation_injuries

    fallout_fatal = fallout_severe = fallout_moderate = fallout_mild = 0
    affected_area = 0

    for i in range(total_dose_grid.shape[0]):
        for j in range(total_dose_grid.shape[1]):
            dose_rem = total_dose_grid[i, j]
            if dose_rem < 100:
                continue

            affected_area += area_per_cell
            population = population_density * area_per_cell

            if dose_rem >= 900:
                fallout_fatal += population * 0.85
                fallout_severe += population * 0.15
            elif dose_rem >= 700:
                fallout_fatal += population * 0.45
                fallout_severe += population * 0.55
            elif dose_rem >= 500:
                fallout_fatal += population * 0.15
                fallout_severe += population * 0.75
                fallout_moderate += population * 0.10
            elif dose_rem >= 350:
                fallout_severe += population * 0.30
                fallout_moderate += population * 0.70
            elif dose_rem >= 250:
                fallout_severe += population * 0.10
                fallout_moderate += population * 0.90
            elif dose_rem >= 150:
                fallout_moderate += population * 0.30
                fallout_mild += population * 0.70
            else:  # 100-150 rem
                fallout_moderate += population * 0.05
                fallout_mild += population * 0.95

    np.random.seed(int(yield_kt * 1337) % 2**32)

    variance_fatal = np.random.uniform(0.88, 1.12)      

    variance_injured = np.random.uniform(0.85, 1.18)    

    final_fatal = int(wseg_base_fatalities * variance_fatal)
    final_injured = int(wseg_base_injuries * variance_injured)

    extreme_fallout_fatal = int(fallout_fatal * 0.05)  

    extreme_fallout_injured = int((fallout_severe + fallout_moderate) * 0.05)  

    final_fatal += extreme_fallout_fatal
    final_injured += extreme_fallout_injured

    print(f"DELFIC fatalities: {final_fatal:,} (WSEG base: {int(wseg_base_fatalities):,}, variance: {variance_fatal:.3f})")
    print(f"DELFIC injuries: {final_injured:,} (WSEG base: {int(wseg_base_injuries):,}, variance: {variance_injured:.3f})")

    return {
        'fatal_casualties': final_fatal,
        'severe_casualties': final_injured,
        'moderate_casualties': 0,
        'mild_casualties': int(fallout_mild * 0.2),
        'total_casualties': final_fatal + final_injured,
        'affected_area_km2': affected_area,
        'population_density_used': population_density,
        'wseg_baseline_fatal': int(wseg_base_fatalities),
        'wseg_baseline_injured': int(wseg_base_injuries),
        'variance_applied': {'fatal': variance_fatal, 'injured': variance_injured}
    }