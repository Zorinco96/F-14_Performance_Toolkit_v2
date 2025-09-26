import pandas as pd
import numpy as np

class ClimbModel:
    """F-14 Climb Performance Model."""

    def __init__(self):
        self.climb_data = pd.read_csv("data/f14_climb_profiles.csv")

    def _interpolate(self, df, weight, alt_ft):
        w = np.clip(weight, df["weight"].min(), df["weight"].max())
        alt = np.clip(alt_ft, df["alt_ft"].min(), df["alt_ft"].max())
        subset = df[(df["weight"] == w)]
        return np.interp(alt, subset["alt_ft"], subset.iloc[:, -1])

    def calculate_climb(self, weight, alt_ft, temp_c, flap="CLEAN", thrust="MIL"):
        roc_vs = self._interpolate(self.climb_data, weight, alt_ft)
        profiles = {
            "best_roc": {"speed_kcas": 350, "vs_fpm": int(roc_vs), "fuel_flow_pph_per_engine": 8000},
            "best_range": {"speed_kcas": 300, "vs_fpm": int(roc_vs*0.85), "fuel_flow_pph_per_engine": 7500},
            "best_endurance": {"speed_kcas": 250, "vs_fpm": int(roc_vs*0.7), "fuel_flow_pph_per_engine": 7000},
            "shortest_time": {"speed_kcas": 400, "vs_fpm": int(roc_vs*0.95), "fuel_flow_pph_per_engine": 9000}
        }

        climb_gradient = roc_vs / (350 * 101.27 / 60)
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
