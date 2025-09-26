import pandas as pd
import numpy as np

class F14Aero:
    """
    Aerodynamic model for the F-14.
    Loads NATOPS-based polar data from f14_aero.csv and provides lookups.
    """

    def __init__(self, csv_path: str):
        self.data = pd.read_csv(csv_path)
        self._validate()

    def _validate(self):
        required_cols = ["config", "sweep", "mach", "clmax", "cd0", "k", "stall_aoa_deg", "l_d_max"]
        for col in required_cols:
            if col not in self.data.columns:
                raise ValueError(f"Missing required column in f14_aero.csv: {col}")

    def polar(self, config: str, mach: float, auto: bool = True):
        """
        Returns aerodynamic polar parameters for given configuration and Mach.
        Interpolates between data points if necessary.

        Args:
            config: "CLEAN", "MANEUVER", or "FULL"
            mach: Mach number (0.2–2.0)
            auto: if True, interpolate smoothly, else pick nearest row

        Returns:
            dict with clmax, cd0, k, stall_aoa_deg, l_d_max
        """
        df = self.data[self.data["config"].str.upper() == config.upper()]
        if df.empty:
            raise ValueError(f"No aerodynamic data found for config {config}")

        if auto:
            clmax = np.interp(mach, df["mach"], df["clmax"])
            cd0 = np.interp(mach, df["mach"], df["cd0"])
            k = np.interp(mach, df["mach"], df["k"])
            stall_aoa = np.interp(mach, df["mach"], df["stall_aoa_deg"])
            l_d = np.interp(mach, df["mach"], df["l_d_max"])
        else:
            row = df.iloc[(df["mach"] - mach).abs().argsort().iloc[0]]
            clmax, cd0, k, stall_aoa, l_d = row[["clmax", "cd0", "k", "stall_aoa_deg", "l_d_max"]]

        return {
            "config": config.upper(),
            "mach": mach,
            "clmax": round(clmax, 3),
            "cd0": round(cd0, 5),
            "k": round(k, 5),
            "stall_aoa_deg": round(stall_aoa, 1),
            "l_d_max": round(l_d, 1)
        }
