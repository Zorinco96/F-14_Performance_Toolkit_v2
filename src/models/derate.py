# Advanced Derate Policy for F-14 Performance Toolkit
# Hybrid model: JSON guardrails + NATOPS/CSV performance validation
# Includes AEO/OEI climb checks, iterative RPM bumping, safety factor, and fuel savings

import json
import os
from data_loaders import load_takeoff_data
from src.models.takeoff_model import calc_takeoff

# Path to derate configuration JSON
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../../data/derate_config.json")

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def validate_derate(weight, temp, pressure, flap_setting, requested_rpm_pct):
    """
    Validates derated thrust setting against policy + NATOPS performance data.

    :param weight: Aircraft weight (lbs)
    :param temp: Ambient OAT (C)
    :param pressure: Baro Pressure (inHg)
    :param flap_setting: UP, MAN, FULL
    :param requested_rpm_pct: Pilot-requested derate RPM % (e.g. 92)
    :return: dict with validated derate outputs (RPM, FF, TODR, ASD, climb data, fuel savings)
    """
    cfg = load_config()

    # Policy floors per flap setting
    flap_floor_map = cfg.get("flap_floor_pct", {"UP": 85, "MAN": 90, "FULL": 95})
    min_rpm_pct = flap_floor_map.get(flap_setting, cfg.get("min_takeoff_rpm_pct", 85))

    rpm_pct = max(requested_rpm_pct, min_rpm_pct)
    safety_factor = cfg.get("safety_factor", 1.10)

    # Iteratively bump RPM until climb requirements are satisfied
    max_rpm = 100
    climb_valid_aeo = False
    climb_valid_oei = False
    while rpm_pct <= max_rpm:
        perf = calc_takeoff(weight, temp, pressure, "REDUCED", flap_setting)
        climb_grad = perf.get("ClimbGradient", 0)

        # Placeholder: treat AEO as reported gradient, OEI as half
        climb_grad_aeo = climb_grad
        climb_grad_oei = climb_grad * 0.5

        climb_valid_aeo = climb_grad_aeo >= 300
        climb_valid_oei = climb_grad_oei >= 200

        if climb_valid_aeo and climb_valid_oei:
            break
        rpm_pct += 1

    status = "Derate accepted." if (climb_valid_aeo and climb_valid_oei) else "Max MIL required."

    # Estimate fuel flow (placeholder scaling)
    idle_ff = cfg.get("idle_ff_pph", 3000)
    max_ff = cfg.get("mil_ff_pph", 10000)
    ff = idle_ff + (rpm_pct / 100.0) * (max_ff - idle_ff)

    # Fuel savings compared to full MIL
    fuel_saving = max_ff - ff

    # TODR/ASD with safety factor
    asd = perf.get("ASD", 7000) * safety_factor
    todr = perf.get("TODR", 7500) * safety_factor

    return {
        "RequestedRPM": requested_rpm_pct,
        "ValidatedRPM": rpm_pct,
        "FuelFlow": ff,
        "FuelSaved": fuel_saving,
        "Flaps": flap_setting,
        "ASD": asd,
        "TODR": todr,
        "ClimbGradientAEO": climb_grad_aeo,
        "ClimbGradientOEI": climb_grad_oei,
        "ClimbValidAEO": climb_valid_aeo,
        "ClimbValidOEI": climb_valid_oei,
        "Status": status
    }

def get_policy_snapshot():
    """Return a snapshot of derate policy settings."""
    return load_config()
