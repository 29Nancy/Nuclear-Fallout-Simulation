

import numpy as np

ATMOSPHERE_DATA = np.array([
    [0.0, 288.15, 101325.0, 1.2250, 1.789e-5],
    [1.0, 281.65, 89874.6,  1.1116, 1.758e-5],
    [2.0, 275.15, 79495.2,  1.0065, 1.726e-5],
    [3.0, 268.65, 70108.5,  0.9091, 1.694e-5],
    [4.0, 262.15, 61640.2,  0.8191, 1.661e-5],
    [5.0, 255.65, 54019.9,  0.7361, 1.628e-5],
    [6.0, 249.15, 47181.0,  0.6597, 1.595e-5],
    [7.0, 242.65, 41060.6,  0.5895, 1.561e-5],
    [8.0, 236.15, 35599.6,  0.5252, 1.527e-5],
    [9.0, 229.65, 30742.6,  0.4663, 1.493e-5],
    [10.0, 223.15, 26436.3, 0.4127, 1.458e-5],
    [11.0, 216.65, 22632.1, 0.3639, 1.422e-5],
    [12.0, 216.65, 19330.4, 0.3108, 1.422e-5],
    [13.0, 216.65, 16510.4, 0.2655, 1.422e-5],
    [14.0, 216.65, 14101.4, 0.2269, 1.422e-5],
    [15.0, 216.65, 12044.8, 0.1938, 1.422e-5],
    [16.0, 216.65, 10289.1, 0.1656, 1.422e-5],
    [17.0, 216.65, 8787.9,  0.1415, 1.422e-5],
    [18.0, 216.65, 7500.2,  0.1209, 1.422e-5],
    [19.0, 216.65, 6401.1,  0.1032, 1.422e-5],
    [20.0, 216.65, 5474.9,  0.0880, 1.422e-5]
])

def get_atmospheric_properties(altitude_m):
    """
    Interpolates atmospheric properties for a given altitude.
    Altitude should be in meters.
    Returns a dictionary of properties.
    """
    altitude_km = altitude_m / 1000.0
    
    # Use numpy's interpolation function
    altitudes = ATMOSPHERE_DATA[:, 0]
    
    # Handle cases outside the data range by clamping to the nearest edge
    if altitude_km <= altitudes[0]:
        return {
            'temperature_k': ATMOSPHERE_DATA[0, 1],
            'pressure_pa': ATMOSPHERE_DATA[0, 2],
            'density_kg_m3': ATMOSPHERE_DATA[0, 3],
            'viscosity_pa_s': ATMOSPHERE_DATA[0, 4]
        }
    if altitude_km >= altitudes[-1]:
        return {
            'temperature_k': ATMOSPHERE_DATA[-1, 1],
            'pressure_pa': ATMOSPHERE_DATA[-1, 2],
            'density_kg_m3': ATMOSPHERE_DATA[-1, 3],
            'viscosity_pa_s': ATMOSPHERE_DATA[-1, 4]
        }
        
    temp = np.interp(altitude_km, altitudes, ATMOSPHERE_DATA[:, 1])
    pressure = np.interp(altitude_km, altitudes, ATMOSPHERE_DATA[:, 2])
    density = np.interp(altitude_km, altitudes, ATMOSPHERE_DATA[:, 3])
    viscosity = np.interp(altitude_km, altitudes, ATMOSPHERE_DATA[:, 4])
    
    return {
        'temperature_k': temp,
        'pressure_pa': pressure,
        'density_kg_m3': density,
        'viscosity_pa_s': viscosity
    }