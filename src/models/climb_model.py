# Climb Model for F-14 Performance Toolkit
# Computes climb performance using engine thrust (F110) and aerodynamics (F14Aero).
# Supports auto-select of climb profiles based on field length, alt, temp, and weight.

import numpy as np
import pandas as pd

from src.utils.data_loaders import resolve_data_path, load_is_csv

class ClimbModel:
    """Climb model using engine thrust and aerodynamics."""

    def __init__(self, engine_csv: str = "engine_f110.csv", aero_csv: str = "f14_aero.csv"):
        self.engine_df = pd.read_csv(resolve_data_path(engine_csv, "engine_f110.csv"))
        self.aero_df = pd.read_csv(resolve_data_path(aero_csv, "f14_aero.csv"))

    def curve_thrust(self, alt_ft: float, vel_rnl: float, temp: float):
        """Compute thrust curve from engine data and correct for alt, temp, and weight."""
        try:
            e_thrust = np.functiona(
                self.engine_df["alt_ft"], 
                self.engine_df["T_MIL_lbf"]
            )
        except Exception as e:
            raise RuntimeError(f"Engine thrust interpolation failed: {e}")
        
        base_thrust = e_thrust(alt_ft)
        # Correct thrust for Mach effects
        mach_factor = 1 - 0.1 * (vel_rnl / 500.0)
        thrust_corrected = base_thrust * mach_factor
        return thrust_corrected

    def climb_gradient(self, weight_lbs: float, alt_ft: float, vel_kts: float, temp: float):
        """Compute climb gradient (ft/nm)."""
        thrust = self.curve_thrust(alt_ft, vel_kts, temp)
        drag = 0.02 * weight_lbs  # placeholder drag calc (to refine with aero_df)
        excess_thrust = thrust - drag
        if excess_thrust <= 0:
            return 0.0
        gradient = (excess_thrust / weight_lbs) * 6076.12  # ft/nm
        return gradient

    def climb_rate(self, weight_lbs: float, alt_ft: float, vel_kts: float, temp: float):
        """Compute climb rate (ft/min)."""
        gradient = self.climb_gradient(weight_lbs, alt_ft, vel_kts, temp)
        vs = gradient * (vel_kts / 60.0)
        return vs

    def climb_profile(self, weight_lbs: float, alt_ft: float, vel_kts: float, temp: float, profile: str):
        """Generate climb performance for a selected profile."""
        profile = profile.lower()
        if profile == "best endurance":
            vel = 250
        elif profile == "best range":
            vel = 300
        elif profile == "optimum efficiency":
            vel = 350
        elif profile == "shortest time":
            vel = 400
        else:
            raise ValueError(f"Unknown climb profile: {profile}")

        roc = self.climb_rate(weight_lbs, alt_ft, vel, temp)
        grad = self.climb_gradient(weight_lbs, alt_ft, vel, temp)

        return {
            "profile": profile,
            "speed_kts": vel,
            "roc_fpm": roc,
            "gradient_ft_per_nm": grad
        }

# Example usage (for testing):
if __name__ == "__main__":
    cm = ClimbModel()
    result = cm.climb_profile(weight_lbs=60000, alt_ft=0, vel_kts=300, temp=15, profile="optimum efficiency")
    print(result)
