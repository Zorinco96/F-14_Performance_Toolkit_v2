# Cruise Model for F-14 Performance Toolkit (Refined)
# Computes realistic cruise performance with fuel burn dynamics, step climbs, accurate TAS/Mach, drag rise, and reserve fuel logic.

import numpy as np
from src.models.engine_model import F110Engine
from src.models.f14_aero import F14Aero

class CruiseModel:
    def __init__(self, engine_type="F110", reserve_fuel=2000):
        if engine_type.upper() != "F110":
            raise ValueError("Currently only F110 engine supported.")
        self.engine = F110Engine()
        self.aero = F14Aero()
        self.reserve_fuel = reserve_fuel

    def _cruise_point(self, weight_lbf, alt_ft, mach, mode="MIL", config="UP"):
        """Compute cruise performance for one Mach/alt point."""
        rho, T = self._isa_atmosphere(alt_ft)
        a = np.sqrt(1.4 * 287.05 * T) * 3.281  # speed of sound (ft/s)
        TAS = mach * a / 1.687  # kts

        perf = self.engine.compute(alt_ft, 15, mach, mode)  # assume ISA temp
        thrust = perf["Thrust"]
        ff = perf["FuelFlow"]

        polar = self.aero.polar(config, sweep=20, mach=mach)
        CLreq = self.aero.lift_coeff(weight_lbf, rho, TAS * 1.687)
        CD = self.aero.drag_coeff(CLreq, polar["CD0"], polar["k"])

        drag = 0.5 * rho * (TAS * 1.687)**2 * self.aero.wing_area * CD

        # Transonic drag rise
        if mach > 0.9:
            drag *= 1 + 0.25 * (mach - 0.9) * 10  # +25% per 0.1 Mach above 0.9

        balance = thrust - drag
        return {
            "Mach": mach,
            "Altitude": alt_ft,
            "TAS": TAS,
            "FuelFlow": ff,
            "Thrust": thrust,
            "Drag": drag,
            "ThrustMargin": balance,
        }

    def compute_profiles(self, weight_lbf, fuel_lbs, alt_ft):
        """Simulate cruise with step climbs and fuel burn dynamics."""
        results = []
        profiles = {
            "BestEndurance": {"mach": 0.4},
            "BestRange": {"mach": 0.7},
            "OptimumEfficiency": {"mach": 0.8},
            "ShortestTime": {"mach": 0.9},
        }

        usable_fuel = fuel_lbs - self.reserve_fuel
        if usable_fuel <= 0:
            return [{"Warning": "Insufficient fuel above reserve"}]

        for pname, pdata in profiles.items():
            mach = pdata["mach"]
            fuel = usable_fuel
            time_hr = 0
            distance_nm = 0
            steps = []
            alt = alt_ft

            while fuel > 0:
                point = self._cruise_point(weight_lbf, alt, mach)
                if point["ThrustMargin"] <= 0:
                    steps.append({"Warning": "Insufficient thrust margin"})
                    break

                burn_hr = point["FuelFlow"]
                if burn_hr <= 0:
                    break

                dt_hr = 0.1  # 6 min step
                fuel_burn = burn_hr * dt_hr
                if fuel_burn > fuel:
                    dt_hr = fuel / burn_hr
                    fuel_burn = fuel

                fuel -= fuel_burn
                weight_lbf -= fuel_burn
                distance_nm += point["TAS"] * dt_hr
                time_hr += dt_hr

                # Step climb logic: simple weight-altitude relation
                opt_alt = 25000 + (60000 - weight_lbf) / 20
                if opt_alt > alt + 2000 and alt < 45000:
                    alt += 2000
                    steps.append({"StepClimb": f"Climb to {alt} ft"})

            results.append({
                "Profile": pname,
                "StartAlt": alt_ft,
                "EndAlt": alt,
                "Mach": mach,
                "Endurance_hr": time_hr,
                "Range_nm": distance_nm,
                "ReserveFuel": self.reserve_fuel,
                "Steps": steps,
            })
        return results

    def _isa_atmosphere(self, alt_ft):
        """Return air density (slugs/ft³) and temperature (K)."""
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
        return rho / 515.378818, T
