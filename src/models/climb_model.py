import pandas as pd
import numpy as np

class ClimbModel:
    """
    F-14 Climb Performance Model.
    Uses NATOPS-based datasets to generate climb profiles and check gradients.
    """

    def __init__(self):
        self.climb_data = pd.read_csv("data/f14_climb_profiles.csv")

    def _interpolate(self, df, weight, alt_ft):
        """
        Helper to interpolate climb performance by weight and altitude.
        """
        w = np.clip(weight, df["weight"].min(), df["weight"].max())
        alt = np.clip(alt_ft, df["alt_ft"].min(), df["alt_ft"].max())
        subset = df[(df["weight"] == w)]
        return np.interp(alt, subset["alt_ft"], subset.iloc[:, -1])

    def calculate_climb(self, weight, alt_ft, temp_c, flap="CLEAN", thrust="MIL"):
        """
        Calculate climb profiles for different optimization strategies.
        """
        profiles = {}

        # Best ROC (Rate of Climb)
        roc_speed = 350  # KCAS typical
        roc_vs = self._interpolate(self.climb_data, weight, alt_ft)
        roc_ff = 8000  # pph/engine placeholder
        profiles["best_roc"] = {
            "speed_kcas": roc_speed,
            "vs_fpm": int(roc_vs),
            "fuel_flow_pph_per_engine": int(roc_ff)
        }

        # Best Range
        range_speed = 300
        range_vs = roc_vs * 0.85
        range_ff = 7500
        profiles["best_range"] = {
            "speed_kcas": range_speed,
            "vs_fpm": int(range_vs),
            "fuel_flow_pph_per_engine": int(range_ff)
        }

        # Best Endurance
        endurance_speed = 250
        endurance_vs = roc_vs * 0.7
        endurance_ff = 7000
        profiles["best_endurance"] = {
            "speed_kcas": endurance_speed,
            "vs_fpm": int(endurance_vs),
            "fuel_flow_pph_per_engine": int(endurance_ff)
        }

        # Shortest Time
        shortest_speed = 400
        shortest_vs = roc_vs * 0.95
        shortest_ff = 9000
        profiles["shortest_time"] = {
            "speed_kcas": shortest_speed,
            "vs_fpm": int(shortest_vs),
            "fuel_flow_pph_per_engine": int(shortest_ff)
        }

        # Check climb gradient
        climb_gradient = roc_vs / (roc_speed * 101.27 / 60)  # ft/nm approx
        gradient_flag = None
        if climb_gradient < 200:
            gradient_flag = "❌ Unsafe: <200 ft/nm"
        elif climb_gradient < 300:
            gradient_flag = "⚠️ Marginal: <300 ft/nm"

        return {
            "weight": weight,
            "alt_ft": alt_ft,
            "flap": flap,
            "thrust": thrust,
            "profiles": profiles,
            "climb_gradient_ft_per_nm": round(climb_gradient, 1),
            "gradient_flag": gradient_flag
        }
