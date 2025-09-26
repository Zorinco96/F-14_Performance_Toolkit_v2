"""
takeoff_model.py

F-14 Takeoff Performance Model
--------------------------------
Implements NATOPS-based takeoff logic for the F-14 Tomcat
using F110 (F-14B/D) or TF30 (F-14A) engines.

Features:
- Computes V1, Vr, V2, Vfs from NATOPS tables.
- Supports thrust modes: MILITARY, AFTERBURNER, REDUCED (manual % RPM).
- Auto-thrust derate selects minimum thrust satisfying climb gradient.
- Flap auto-select logic based on weight/runway.
- Ensures climb gradient ≥ 300 ft/nm (amber caution if < 300, red if < 200).
- Outputs thrust type, RPM, FF per engine, flap setting, trim, V-speeds, climb VS.
"""

import numpy as np
import pandas as pd
from src.models.engine_model import EngineModel
from src.models.f14_aero import AeroModel

class TakeoffModel:
    def __init__(self, engine: EngineModel, aero: AeroModel, vspeed_table: str, refusal_file: str):
        self.engine = engine
        self.aero = aero
        self.vspeeds = pd.read_csv(vspeed_table)
        self.refusal = pd.read_csv(refusal_file)

    def interpolate_vspeeds(self, weight, flap):
        df = self.vspeeds[self.vspeeds["flap"] == flap]
        v1 = np.interp(weight, df["weight"], df["V1"])
        vr = np.interp(weight, df["weight"], df["Vr"])
        v2 = np.interp(weight, df["weight"], df["V2"])
        vfs = np.interp(weight, df["weight"], df["Vfs"])
        return v1, vr, v2, vfs

    def select_flaps(self, weight, mode="AUTO", user_flaps=None):
        if mode != "AUTO":
            return user_flaps
        if weight < 50000:
            return "UP"
        elif weight < 62000:
            return "MANEUVER"
        else:
            return "FULL"

    def required_thrust(self, weight, field_elev, oat, runway_length, flap, thrust_mode="AUTO", user_derate=None):
        if thrust_mode == "MILITARY":
            rpm, ff = self.engine.get_mil_thrust(oat, field_elev)
            mode = "MILITARY"
        elif thrust_mode == "AFTERBURNER":
            rpm, ff = self.engine.get_ab_thrust(oat, field_elev)
            mode = "AFTERBURNER"
        elif thrust_mode == "REDUCED":
            rpm, ff = self.engine.get_derated_thrust(user_derate, oat, field_elev)
            mode = f"REDUCED ({user_derate:.0f}% RPM)"
        elif thrust_mode == "AUTO":
            for derate in range(85, 101):
                rpm, ff = self.engine.get_derated_thrust(derate, oat, field_elev)
                grad = self.estimate_climb_gradient(weight, flap, rpm, oat, field_elev)
                if grad >= 300:
                    mode = f"REDUCED ({derate:.0f}% RPM)"
                    break
            else:
                rpm, ff = self.engine.get_mil_thrust(oat, field_elev)
                grad = self.estimate_climb_gradient(weight, flap, rpm, oat, field_elev)
                if grad >= 200:
                    mode = "MILITARY (CAUTION <300 ft/nm)"
                else:
                    rpm, ff = self.engine.get_ab_thrust(oat, field_elev)
                    mode = "AFTERBURNER (REQUIRED, <200 ft/nm)"
        else:
            raise ValueError("Invalid thrust mode")

        return mode, rpm, ff

    def estimate_climb_gradient(self, weight, flap, rpm, oat, field_elev):
        thrust = self.engine.thrust_from_rpm(rpm, oat, field_elev)
        ld_ratio = self.aero.get_ld_ratio(flap)
        excess_thrust = thrust - weight / ld_ratio
        grad = (excess_thrust / weight) * 6076
        return grad

    def compute_takeoff(self, weight, field_elev, oat, runway_length,
                        thrust_mode="AUTO", user_derate=None, flap_mode="AUTO", user_flaps=None):
        flap = self.select_flaps(weight, flap_mode, user_flaps)
        v1, vr, v2, vfs = self.interpolate_vspeeds(weight, flap)
        thrust_type, rpm, ff = self.required_thrust(weight, field_elev, oat, runway_length,
                                                    flap, thrust_mode, user_derate)
        trim = f"Trim for {v2:.0f}–{v2+15:.0f} KCAS (gear up)"
        grad = self.estimate_climb_gradient(weight, flap, rpm, oat, field_elev)
        roc = (grad / 6076) * (v2 * 1.687) * 60
        return {
            "Flaps": flap,
            "ThrustType": thrust_type,
            "RPM": f"{rpm:.0f}%",
            "FF_per_engine": f"{ff:.0f} pph",
            "V1": f"{v1:.0f} KCAS",
            "Vr": f"{vr:.0f} KCAS",
            "V2": f"{v2:.0f} KCAS",
            "Vfs": f"{vfs:.0f} KCAS",
            "Trim": trim,
            "ClimbVS": f"{roc:.0f} ft/min"
        }
