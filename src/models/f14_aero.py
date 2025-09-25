"""
Refined Aerodynamic Model for F-14 Tomcat
Aligned with expanded NATOPS-style aero dataset (f14_aero.csv)

Enhancements:
- Auto-sweep scheduling (if auto=True)
- Effective wing area scaling with sweep angle
- Stall speed & best glide speed helper functions
"""

import pandas as pd
import numpy as np
from src.data_loaders import resolve_data_path

class F14Aero:
    def __init__(self, csv_file="data/f14_aero.csv"):
        self.csv_file = resolve_data_path(csv_file)
        self.df = pd.read_csv(self.csv_file)

        # Normalize column names
        self.df.columns = [c.lower() for c in self.df.columns]

        # Validate columns
        required = {"config", "sweep", "mach", "clmax", "cd0", "k"}
        if not required.issubset(set(self.df.columns)):
            raise ValueError(f"Aero CSV missing required columns: {required - set(self.df.columns)}")

        # Reference wing area (ft², unswept)
        self.wing_area_ref = 565.0

    def _nearest_config(self, config: str):
        """Filter dataset for given config (default CLEAN if not found)."""
        config = config.upper()
        if config not in self.df["config"].unique():
            config = "CLEAN"
        return self.df[self.df["config"] == config]

    def _auto_sweep(self, mach: float) -> float:
        """Approximate NATOPS auto-sweep schedule (deg)."""
        if mach < 0.6:
            return 20
        elif mach < 0.9:
            return 35
        elif mach < 1.2:
            return 55
        else:
            return 68

    def polar(self, config: str, sweep: float = 20, mach: float = 0.2, auto: bool = False):
        """
        Return aerodynamic coefficients for given config, sweep, and Mach.
        Performs nearest-match sweep and interpolates across Mach levels.
        """
        if auto:
            sweep = self._auto_sweep(mach)

        sub_df = self._nearest_config(config)

        # Nearest sweep available
        sweeps = np.array(sub_df["sweep"].unique())
        nearest_sweep = sweeps[np.abs(sweeps - sweep).argmin()]
        sub_df = sub_df[sub_df["sweep"] == nearest_sweep]

        # Interpolate in Mach space
        mach_values = sub_df["mach"].values
        result = {}
        for col in ["clmax", "cd0", "k", "stall_aoa_deg", "l_d_max"]:
            result[col] = float(np.interp(mach, mach_values, sub_df[col].values))

        # Scale wing area with sweep
        sweep_rad = np.radians(nearest_sweep)
        result["wing_area_eff"] = self.wing_area_ref * np.cos(sweep_rad)

        return result

    def stall_speed(self, weight: float, rho: float, config: str, sweep: float = 20, mach: float = 0.2, auto: bool = False):
        """Compute stall speed (ft/s) for given weight & density."""
        polar = self.polar(config, sweep, mach, auto=auto)
        CLmax = polar["clmax"]
        S = polar["wing_area_eff"]
        Vstall = np.sqrt((2 * weight) / (rho * S * CLmax))
        return Vstall

    def best_glide_speed(self, weight: float, rho: float, config: str, sweep: float = 20, mach: float = 0.6, auto: bool = False):
        """Compute best glide speed (ft/s) from L/Dmax."""
        polar = self.polar(config, sweep, mach, auto=auto)
        # Approximate best glide CL ~ sqrt(CD0/k)
        CL_best = np.sqrt(polar["cd0"] / polar["k"])
        S = polar["wing_area_eff"]
        V_best = np.sqrt((2 * weight) / (rho * S * CL_best))
        return V_best
