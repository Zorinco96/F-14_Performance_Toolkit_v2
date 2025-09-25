# Cruise Model for F-14 Performance
# Derived from old repo logic, refactored for CSV integration and mission card outputs.

import numpy as np
from data_loaders import load_cruise_data
import isa

def calc_cruise(weight, altitude, mach, thrust_mode):
    """
    Calculate cruise performance using NATOPS data.
    :param weight: Aircraft weight (lbs)
    :param altitude: Cruise altitude (ft)
    :param mach: Cruise Mach number
    :param thrust_mode: MIL, AB, or REDUCED
    :return: Dictionary of cruise performance data
    """
    # Load cruise dataset
    cruise_data = load_cruise_data()

    # Placeholder values until interpolation is implemented
    fuel_flow = 8000  # pph total (placeholder)
    tas = mach * 661  # approx ktas at Mach number at ISA SL (placeholder)
    endurance = 1.5   # hours
    range_nm = tas * endurance

    return {
        "Mach": mach,
        "Altitude": altitude,
        "FuelFlow": fuel_flow,
        "TAS": tas,
        "Endurance": endurance,
        "Range": range_nm,
        "ThrustMode": thrust_mode
    }
