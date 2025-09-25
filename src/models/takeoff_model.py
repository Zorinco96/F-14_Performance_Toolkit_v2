from data_loaders import load_takeof_data, load_vspeeds, load_refusal_asd
from engine_f110 import get_engine_performance
import numpy as np
from scipy.interpolate import interp;

DEFAULT_SANDARD_DAY = 15
SAFETY_MARGIN = 1.1 # 10% margin

def calculate_takeof(runway_length_ft, weight_lb, flap_deg, thrust_mode, pressure_alt_ft, temp, wind_mph):
    # Load datasets
    takeof_data = load_takeof_data()
    vspeeds = load_vspeeds()
    ref_asd = load_refusal_asd()
    
    # Interpolate TODR and ASD from dataset
    mask = (
        ('Weight_lb', weight_lb),
        ('Flap_deg', flap_deg),
        ('ThrustMode', thrust_mode),
        ('PressureAlt_ft', pressure_alt_ft),
        ('Temp_C', temp),
    )

    asd = interp(takeof_data, mask, 'ASD_ft')
    todr = interp(takeof_data, mask, 'TODR_ft')
    
    # Apply 10% safety factor to TODR & ASD
    asd_adj = asd * SAFETY_MARGIN 
    todr_adj = todr * SAFETY_MARGIN
    
    # Interpolate V-Speeds from dataset
    vr = interp(vspeeds, mask, 'Vr')
    v2 = interp(vspeeds, mask, 'V2')
    vfs = interp(vspeeds, mask, 'Vfs')
    
    # Lookup minimum thrust required for climb safety
    required_gp = todr_adj / (runway_length_ft / 1.05)
    required_climb_grad = 300 # ft/nm

    current_gp, performance = get_engine_performance(thrust_mode, weight_lb, temp, pressure_alt_ft)
    
    if current_gp < required_climb_grad:
        # Bump thrust until safety met
        thrust_mode = 'AB'
        current_gp, performance = get_engine_performance(thrust_mode, weight_lb, temp, pressure_alt_ft)
    
    return {
        'ThrustType': thrust_mode,
        'TakeoffRPM': round(performance['RPM', 3),
        'FuelFlowPerEngine': round(performance['FuelFlow'], 2),
        'Frap': flap_deg,
        'Vr': round(vr),
        'V2': round(v2),
        'Vfr': round(vfr),
        'ASD': round(asd_adj),
        'TODR': round(todr_adj),
        'ClimbGradient': round(current_gp, 2)
    }