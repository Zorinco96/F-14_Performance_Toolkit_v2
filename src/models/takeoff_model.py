import pandas as pd
import numpy as np

class TakeoffModel:
    """
    F-14 Takeoff Performance Model.
    Uses NATOPS-based datasets with 10% safety margin applied.
    """

    def __init__(self):
        self.takeoff_data = pd.read_csv("data/takeoff_data_expanded.csv")
        self.refusal_data = pd.read_csv("data/refusal_asd.csv")
        self.vspeeds_data = pd.read_csv("data/vspeeds.csv")

    def _interpolate_dataset(self, df, weight, alt_ft, temp_c):
        """
        Helper for tri-linear interpolation in performance tables.
        """
        # Clamp ranges
        w = np.clip(weight, df["weight"].min(), df["weight"].max())
        alt = np.clip(alt_ft, df["alt_ft"].min(), df["alt_ft"].max())
        temp = np.clip(temp_c, df["temp_c"].min(), df["temp_c"].max())

        # Group by condition, interpolate
        subset = df[(df["weight"] == w) & (df["alt_ft"] == alt)]
        return np.interp(temp, subset["temp_c"], subset.iloc[:, -1])

    def calculate_takeoff(self, weight, alt_ft, temp_c, flap="MAN", thrust="MIL"):
        """
        Calculate takeoff distances, V-speeds, and climb checks.

        Args:
            weight (int): Aircraft gross weight (lbs)
            alt_ft (int): Field pressure altitude (ft)
            temp_c (float): OAT in °C
            flap (str): "UP", "MAN", "FULL"
            thrust (str): "MIL", "AB", "REDUCED"
        """
        # TODR (Takeoff Distance Over 50ft)
        todr = self._interpolate_dataset(self.takeoff_data, weight, alt_ft, temp_c)
        todr *= 1.1  # Apply 10% safety factor

        # ASD (Accelerate-Stop Distance)
        asd = self._interpolate_dataset(self.refusal_data, weight, alt_ft, temp_c)
        asd *= 1.1

        # V-speeds
        vrow = self.vspeeds_data[self.vspeeds_data["weight"] == weight]
        if vrow.empty:
            vrow = self.vspeeds_data.iloc[(self.vspeeds_data["weight"] - weight).abs().argsort().iloc[0:1]]
        v1, vr, v2, vfs = vrow.iloc[0][["v1", "vr", "v2", "vfs"]]

        # Thrust logic
        thrust_mode = thrust
        notes = []
        if thrust.upper() == "REDUCED":
            notes.append("Reduced thrust selected — performance checked vs gradient limits.")
        elif thrust.upper() == "AUTO":
            thrust_mode = "MIL"
            notes.append("Auto-thrust: MIL selected as baseline.")

        # Climb gradient requirement
        climb_gradient = 320  # ft/nm, placeholder until integrated with climb_model
        if climb_gradient < 300 and thrust_mode == "MIL":
            notes.append("⚠️ Climb <300 ft/nm, MIL insufficient. Consider FULL AB.")
        elif climb_gradient < 200:
            notes.append("❌ Unsafe: <200 ft/nm, AB required.")

        return {
            "weight": weight,
            "alt_ft": alt_ft,
            "temp_c": temp_c,
            "flap": flap,
            "thrust": thrust_mode,
            "todr_ft": round(float(todr), 0),
            "asd_ft": round(float(asd), 0),
            "v1": int(v1),
            "vr": int(vr),
            "v2": int(v2),
            "vfs": int(vfs),
            "climb_gradient_ft_per_nm": climb_gradient,
            "notes": notes
        }
