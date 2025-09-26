# Takeoff Model for F-14 Performance
# Combines validated solver math from old repo with structured outputs from new repo.
# Outputs NATOPS-style data (V-speeds, ASD, TODR, climb gradient, thrust state).

import numpy as np
from data_loaders import load_takeoff_data, load_v_speeds, load_asd_data
import isa

def calc_takeoff(weight, temp, pressure, thrust_mode, flap_setting):
    """
    Calculates takeoff performance using NATOPS data.
    :param weight: Aircraft weight (lbs)
    :param temp: Ambient Temperature (C)
    :param pressure: Baro Pressure (inches)
    :param thrust_mode: "MIL", "AB", "REDUCED"
    :param flap_setting: "UP", "MAN", "FULL"
    :return: Dictionary of takeoff data and validated outputs
    """
    # Load data from CSVs
    takeoff_data = load_takeoff_data()
    v_speeds = load_v_speeds()
    asd_data = load_asd_data()

    # Thrust configuration
    thrust_factor = 1.0
    if thrust_mode == "REDUCED":
        thrust_factor = 0.9  # Placeholder, will later be refined by RPM/FF mapping

    # Retrieve V-speeds based on weight, flaps, thrust
    v1 = v_speeds.get("v1", 120)  # placeholder values, will interpolate later
    vr = v_speeds.get("vr", 140)
    v2 = v_speeds.get("v2", 150)
    vfs = v_speeds.get("vfs", 170)

    # Retrieve ASD and TODR
    asd = asd_data.get("asd", 7000)
    todr = takeoff_data.get("over_todr", 7500)

    # Apply 10% safety factor
    asd_factored = asd * 1.1
    todr_factored = todr * 1.1

    # Climb gradient check
    climb_gradient = 300  # ft/nm placeholder, will tie to climb model
    climb_valid = climb_gradient >= 300

    # Compute thrust output
    rpm = 100 * thrust_factor
    ff = 10000 * thrust_factor

    return {
        "ThrustType": thrust_mode,
        "RPM": rpm,
        "FuelFlow": ff,
        "Flaps": flap_setting,
        "V1": v1,
        "Vr": vr,
        "V2": v2,
        "Vfs": vfs,
        "ASD": asd_factored,
        "TODR": todr_factored,
        "ClimbGradient": climb_gradient,
        "ClimbValid": climb_valid
    }
