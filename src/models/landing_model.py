import pandas as pd
import numpy as np

class LandingModel:
    """
    F-14 Landing Performance Model.
    Uses NATOPS-based datasets with safety factors applied.
    """

    def __init__(self):
        self.landing_data = pd.read_csv("data/f14_landing_natops_full.csv")

    def _interpolate_dataset(self, df, weight, alt_ft, temp_c):
        """
        Helper for tri-linear interpolation in landing tables.
        """
        w = np.clip(weight, df["weight"].min(), df["weight"].max())
        alt = np.clip(alt_ft, df["alt_ft"].min(), df["alt_ft"].max())
        temp = np.clip(temp_c, df["temp_c"].min(), df["temp_c"].max())

        subset = df[(df["weight"] == w) & (df["alt_ft"] == alt)]
        return np.interp(temp, subset["temp_c"], subset.iloc[:, -1])

    def calculate_landing(self, weight, alt_ft, temp_c, flap="FULL"):
        """
        Calculate landing distance and speeds.

        Args:
            weight (int): Landing weight (lbs)
            alt_ft (int): Field pressure altitude (ft)
            temp_c (float): OAT (°C)
            flap (str): "FULL" (default) or "MAN"
        """
        # Base landing distance
        ldr = self._interpolate_dataset(self.landing_data, weight, alt_ft, temp_c)
        ldr *= 1.1  # Apply 10% safety margin

        # Speeds (simplified for NATOPS — could expand by config)
        vref = 130 + (weight - 50000) / 1000 * 2  # approx NATOPS scaling
        vfs = vref + 20
        vac = vref + 10

        # Go-around planning (pattern at ~200 KCAS)
        go_around_thrust = "MIL"
        go_around_speed = 200
        go_around_notes = "Plan for MIL power go-around, pattern speed ~200 KCAS."

        return {
            "weight": weight,
            "alt_ft": alt_ft,
            "temp_c": temp_c,
            "flap": flap,
            "ldr_ft": round(float(ldr), 0),
            "vref": int(vref),
            "vfs": int(vfs),
            "vac": int(vac),
            "go_around_thrust": go_around_thrust,
            "go_around_speed_kcas": go_around_speed,
            "notes": [go_around_notes]
        }
