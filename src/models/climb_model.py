# Climb Model for F-14 Performance Toolkit
# Computes climb performance using engine thrust (F110) and aerodynamics (F14Aero).
# Supports multiple profiles: Best ROC, Best Range, Best Endurance, Shortest Time.

import numpy as np
from src.models.engine_model import F110Engine
from src.models.f14_aero import F14Aero

class ClimbModel:
    def __init__(self, engine_type="F110"):
        if engine_type.upper() != "F110":
            raise ValueError("Currently only F110 engine supported.")
        self.engine = F110Engine()
        self.aero = F14Aero()

    def _block_climb(self, weight_lbf, alt_start, alt_end, temp_c, mach, config="UP", mode="MIL"):
        """Compute climb for one altitude block."""
        rho = self._isa_density(alt_start)
        perf = self.engine.compute(alt_start, temp_c, mach, mode)
        thrust = perf["Thrust"]
        ff = perf["FuelFlow"]

        polar = self.aero.polar(config, sweep=20, mach=mach)
        CLreq = self.aero.lift_coeff(weight_lbf, rho, mach * 661.0 / 1.944)  # approximate V from Mach
        CD = self.aero.drag_coeff(CLreq, polar["CD0"], polar["k"])

        drag = 0.5 * rho * (mach * 661.0)**2 * self.aero.wing_area * CD
        excess = thrust - drag

        # Rate of climb (ft/min)
        ROC = (excess * mach * 661.0) / weight_lbf * 60.0
        GS = mach * 661.0 / 1.687  # knots true approx
        gradient = ROC / GS if GS > 0 else 0

        # Time and fuel
        delta_alt = alt_end - alt_start
        time_min = delta_alt / ROC if ROC > 0 else 999
        fuel_burn = ff * time_min

        return {
            "AltStart": alt_start,
            "AltEnd": alt_end,
            "ROC": ROC,
            "Gradient": gradient,
            "Time": time_min,
            "Distance": GS * time_min / 60.0,
            "Fuel": fuel_burn,
        }

    def compute_profiles(self, weight_lbf, temp_c, alt_max=30000, mach_schedule=[0.4, 0.6, 0.8]):
        """Compute multiple climb profiles up to alt_max."""
        results = []
        alt_blocks = [(0, 5000), (5000, 10000), (10000, 20000), (20000, alt_max)]
        profiles = {
            "BestROC": {"mach": 0.6},
            "BestRange": {"mach": 0.8},
            "BestEndurance": {"mach": 0.4},
            "ShortestTime": {"mach": 0.9},
        }

        for pname, pdata in profiles.items():
            mach = pdata["mach"]
            profile_res = []
            for (a0, a1) in alt_blocks:
                seg = self._block_climb(weight_lbf, a0, a1, temp_c, mach, config="UP", mode="MIL")
                profile_res.append(seg)
            total_time = sum(s["Time"] for s in profile_res)
            total_fuel = sum(s["Fuel"] for s in profile_res)
            total_dist = sum(s["Distance"] for s in profile_res)
            avg_grad = np.mean([s["Gradient"] for s in profile_res])

            # OEI check (half thrust approx)
            oei_grad = avg_grad * 0.5
            valid_aeo = avg_grad >= 300
            valid_oei = oei_grad >= 200

            results.append({
                "Profile": pname,
                "Segments": profile_res,
                "TotalTime": total_time,
                "TotalFuel": total_fuel,
                "TotalDistance": total_dist,
                "AvgGradient": avg_grad,
                "OEIGradient": oei_grad,
                "ValidAEO": valid_aeo,
                "ValidOEI": valid_oei,
            })
        return results

    def _isa_density(self, alt_ft):
        """Return air density at altitude (ISA approx, slug/ft^3)."""
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
        return rho / 515.378818  # convert to slugs/ft^3
