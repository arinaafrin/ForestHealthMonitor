import numpy as np

from src.processing.vegetation_indices import (
    calculate_vegetation_greenness,
    calculate_burn_severity,
    calculate_moister_stress,
    calculate_canopy_density,
    summarize_all_health_indicates
)

def test_healthy_plant_has_high_greenness_score():
    # Healthy leaves reflect a lot of infrared light, and little red light
    nir = np.array([0.5])
    red = np.array([0.1])
    score = calculate_vegetation_greenness(nir, red)
    # print(score)
    assert score[0] > 0.6 
    

def test_bare_soil_has_near_zero_greenness_score():
    # soil reflects red and infrared light almost the same amount
    nir = np.array([0.3])
    red = np.array([0.3])
    score = calculate_vegetation_greenness(nir, red)
    assert abs(score[0]) < 0.05