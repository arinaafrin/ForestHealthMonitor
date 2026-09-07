"""  
Vegetation Index Formulas...
NDVI = Normalized Difference Vegetation Index
NBR  = Normalized Burn Ratio
NDMI = Normalized Difference Moisture Index
EVI  = Enhanced Vegetation Index
EPS  = Epsilon
NIR  = Near-Infrared band
swir = Shortwave Infrared

Input  : Light values from satellite bands (Numbers between 0 and 1)
Output : Health Score
"""
import numpy as np

# Small number, stops (divided by zero) errors
_EPS = 1e-8 

def calculate_vegetation_greenness(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    # NDVI = Plant health score, if higher then healthier and greener plant
    return (nir - red) / (nir + red + _EPS) 

def calculate_burn_severity(nir: np.ndarray, swir2: np.ndarray) -> np.ndarray:
    # NBR = Burn severity score, if lower then worse fire damage
    return (nir - swir2) / (nir + swir2 + _EPS) 

def calculate_moister_stress(nir: np.ndarray, swir1: np.ndarray) -> np.ndarray:
    # NDMI = Plant moisture score, if lower then drier plant
    return (nir - swir1) / (nir + swir1 + _EPS)

def calculate_canopy_density(nir: np.ndarray, red: np.ndarray, blue: np.ndarray) -> np.ndarray:
    # EVI = Dense forest health score, if higher then healthier vegetation
    # Standard EVI coefficients: fix atmospheric haze (6.0, 7.5), soil brightness (1.0), and scale output (2.5)
    gain = 2.5             # scales output to standard range
    red_weight = 6.0       # corrects haze in red light
    blue_weight = 7.5      # corrects blue light scattering
    soil_adjustment = 1.0  # removes soil background noise
    denominator = nir + red_weight * red - blue_weight * blue + soil_adjustment  
    return gain * (nir - red) / (denominator + _EPS) 

def summarize_all_health_indices(bands: dict[str, np.ndarray]) -> dict[str, float]:
    # Processes raw bands into index scores, returning a clean summary dictionary ready for database storage
    return {
        "greenness": float(np.mean(calculate_vegetation_greenness(bands["nir"], bands["red"]))),
        "burn_severity": float(np.mean(calculate_burn_severity(bands["nir"], bands["swir2"]))),
        "moisture_stress": float(np.mean(calculate_moister_stress(bands["nir"], bands["swir1"]))),
        "canopy_density": float(np.mean(calculate_canopy_density(bands["nir"], bands["red"], bands["blue"]))),
    }