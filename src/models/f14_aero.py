# Aerodynamic Model for F-14 Performance Toolkit
# Hybrid approach: CSV data + NATOPS-based defaults for resilience
# Provides lift (CL) and drag (CD) coefficients across Mach, sweep, and flap configs

import numpy as np
import pandas as pd
from data_loaders import resolve_data_path

class F14Aero:
    def __init__(self, csv_file="f14_aero.csv"):
        try:
            self.df = pd.read_csv(resolve_data_path(csv_file))
        except FileNotFoundError:
            self.df = None

        # NATOPS baseline defaults (approximate, for fallback)
        self.defaults = {
            ("UP", 20): {"CLmax": 1.2, "CD0": 0.022, "k": 0.045},
            ("MANEUVER", 20): {"CLmax": 1.6, "CD0": 0.035, "k": 0.055},
            ("FULL", 20): {"CLmax": 2.1, "CD0": 0.055, "k": 0.065},
        }

        self.wing_area = 565.0  # ft²

    def _nearest_config(self, config: str, sweep: float):
        """Get nearest matching config+sweep from CSV or defaults."""
        if self.df is not None:
            sub_df = self.df[self.df["config"] == config.upper()]
            if not sub_df.empty:
                sweeps = sub_df["sweep"].unique()
                nearest_sweep = min(sweeps, key=lambda x: abs(x - sweep))
                row = sub_df[sub_df["sweep"] == nearest_sweep].iloc[0]
                return {
                    "CLmax": row["CLmax"],
                    "CD0": row["CD0"],
                    "k": row["k"],
                    "Sweep": nearest_sweep,
                    "Source": "CSV",
                }

        # Fallback to defaults
        key = (config.upper(), 20)
        if key in self.defaults:
            vals = self.defaults[key]
            return {**vals, "Sweep": 20, "Source": "NATOPS Default"}
        else:
            raise ValueError(f"No aero data for config={config}, sweep={sweep}")

    def polar(self, config: str, sweep: float = 20, mach: float = 0.4):
        """Return CLmax, CD0, k for given flap config, sweep, and Mach."""
        base = self._nearest_config(config, sweep)

        # Apply Mach corrections (placeholder quadratic scaling)
        CLmax = base["CLmax"] * (1 - 0.05 * max(0, mach - 0.9))
        CD0 = base["CD0"] * (1 + 0.25 * mach**2)
        k = base["k"] * (1 + 0.1 * mach)

        return {
            "Config": config.upper(),
            "Sweep": base["Sweep"],
            "CLmax": CLmax,
            "CD0": CD0,
            "k": k,
            "Source": base["Source"],
        }

    def lift_coeff(self, weight_lbf: float, rho: float, V_mps: float):
        """Calculate CL required for steady level flight."""
        q = 0.5 * rho * V_mps**2
        CL = weight_lbf / (q * self.wing_area)
        return CL

    def drag_coeff(self, CL: float, CD0: float, k: float, cd_misc: float = 0.0):
        """Calculate CD for given CL."""
        return CD0 + k * CL**2 + cd_misc
