# Takeoff Model for F-14 Performance Toolkit (Integrated)
# Computes NATOPS-based takeoff performance with engine+aero integration.

import numpy as np
from src.models.engine_model import F110Engine
from src.models.f14_aero import F14Aero
from data_loaders import load_takeoff_data, load_v_speeds, load_asd_data

class TakeoffModel:
    def __init__(self, reserve_factor=1.1):
        self.takeoff_data = load_takeoff_data()
        self.v_speeds = load_v_speeds()
        self.asd_data = load_asd_data()
        self.reserve_factor = reserve_factor
        self.engine = F110Engine()
        self.aero = F14Aero()

    def _interpolate(self, data_dict, key, default=0):
        return data_dict.get(key, default)

    def compute_takeoff(self, weight, alt_ft, oat_c, thrust_mode="MIL", flap_setting="MAN", runway_length=10000, derate_rpm=None):
        """
        Calculate takeoff performance for the F-14.
        
        Parameters:
            weight (float): Aircraft weight in lbs
            alt_ft (float): Field elevation in feet
            oat_c (float): Outside air temperature in Celsius
            thrust_mode (str): MIL, AB, REDUCED
            flap_setting (str): UP, MAN, FULL
            runway_length (float): Runway length in feet
            derate_rpm (float): Manual derate RPM if thrust_mode=REDUCED
        
        Returns:
            dict: Pilot-facing performance data
        """

        mach_to = 0.25  # representative takeoff Mach number

        # --- Engine thrust ---
        if thrust_mode == "REDUCED" and derate_rpm:
            perf = self.engine.compute_from_rpm(alt_ft, oat_c, mach_to, derate_rpm)
        else:
            perf = self.engine.compute(alt_ft, oat_c, mach_to, thrust_mode)

        thrust = perf["Thrust"]
        rpm = perf["RPM"]
        fuel_flow = perf["FuelFlow"]

        # --- Aerodynamics ---
        polar = self.aero.polar(flap_setting, sweep=20, mach=mach_to)
        rho = self._isa_density(alt_ft)
        v_to = np.sqrt((2 * weight) / (rho * self.aero.wing_area * polar["CLmax"]))  # stall speed approx
        vr = 1.2 * v_to
        v2 = 1.3 * v_to
        vfs = 1.4 * v_to
        v1 = max(100, min(vr, 0.95 * vr))  # NATOPS: V1 ≥ Vmcg, ≤ Vr

        # --- ASD & TODR from datasets ---
        asd = self._interpolate(self.asd_data, "asd", 7000)
        todr = self._interpolate(self.takeoff_data, "over_todr", 7500)
        asd *= self.reserve_factor
        todr *= self.reserve_factor

        # --- Climb gradient ---
        drag = 0.5 * rho * (vr * 1.687)**2 * self.aero.wing_area * (
            polar["CD0"] + polar["k"] * (weight / (0.5 * rho * (vr * 1.687)**2 * self.aero.wing_area))**2
        )
        excess_thrust = thrust - drag
        climb_grad_all = (excess_thrust / weight) * 6076  # ft/nm

        # OEI assumption: thrust cut in half
        thrust_oei = 0.5 * thrust
        excess_thrust_oei = thrust_oei - drag
        climb_grad_oei = max(0, (excess_thrust_oei / weight) * 6076)

        # --- Warnings ---
        warnings = []
        if asd > runway_length or todr > runway_length:
            warnings.append("Runway too short for computed ASD/TODR!")
        if climb_grad_all < 300:
            warnings.append("All-engine climb gradient below 300 ft/nm!")
        if climb_grad_oei < 200:
            warnings.append("OEI climb gradient below 200 ft/nm!")

        return {
            "ThrustType": thrust_mode,
            "RPM": rpm,
            "FuelFlow": fuel_flow,
            "Flaps": flap_setting,
            "V1": int(v1),
            "Vr": int(vr),
            "V2": int(v2),
            "Vfs": int(vfs),
            "ASD": int(asd),
            "TODR": int(todr),
            "ClimbGradient_AllEng": int(climb_grad_all),
            "ClimbGradient_OEI": int(climb_grad_oei),
            "RunwayLength": runway_length,
            "Warnings": warnings
        }

    def _isa_density(self, alt_ft):
        """ISA density (slugs/ft³)."""
        alt_m = alt_ft * 0.3048
        T0 = 288.15
        p0 = 101325
        L = 0.0065
        R = 287.05
        g = 9.80665
        if alt_m < 11000:
            T = T0 - L * alt_m
            p = p0 * (T / T0)**(g / (R * L))
        else:
            T = T0 - L * 11000
            p = p0 * (T / T0)**(g / (R * L)) * np.exp(-g * (alt_m - 11000) / (R * T))
        rho = p / (R * T)
        return rho / 515.378818
