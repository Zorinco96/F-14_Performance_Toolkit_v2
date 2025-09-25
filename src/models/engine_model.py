# Refined Engine model for F-14 (F110-GE-400)
# Uses NATOPS-based MIL thrust data + scaling for AB
# Supports RPM <-> thrust mapping for derates

import numpy as np
import pandas as pd
from src.data_loaders import resolve_data_path

class F110Engine:
    def __init__(self, model_csv="data/f110_tff_model.csv"):
        self.model_csv = resolve_data_path(model_csv)
        self.df = pd.read_csv(self.model_csv)

        # Build interpolation functions
        self.altitudes = self.df["alt_ft"].values
        self.mil_thrust = self.df["T_MIL_lbf"].values
        self.mil_ff = self.df["FF_MIL_pph"].values

    def _interp(self, x, x_points, y_points):
        return float(np.interp(x, x_points, y_points))

    def compute(self, alt_ft, oat_c=15, mach=0.0, thrust_mode="MIL"):
        """Compute thrust, RPM, and fuel flow for given mode"""
        mil_thrust = self._interp(alt_ft, self.altitudes, self.mil_thrust)
        mil_ff = self._interp(alt_ft, self.altitudes, self.mil_ff)

        if thrust_mode == "MIL":
            thrust = mil_thrust
            rpm = 99
            ff = mil_ff

        elif thrust_mode == "AB":
            thrust = mil_thrust * 1.65
            rpm = 103
            ff = mil_ff * 1.5

        else:  # Idle approx
            thrust = 3000
            rpm = 71
            ff = 2000

        return {"Thrust": thrust, "RPM": rpm, "FuelFlow": ff}

    def compute_from_rpm(self, alt_ft, oat_c=15, mach=0.0, rpm=95):
        """Compute thrust and FF from a manual RPM setting"""
        mil_thrust = self._interp(alt_ft, self.altitudes, self.mil_thrust)
        mil_ff = self._interp(alt_ft, self.altitudes, self.mil_ff)

        ab_thrust = mil_thrust * 1.65
        ab_ff = mil_ff * 1.5

        # Map rpm points
        rpm_points = np.array([71, 99, 103])
        thrust_points = np.array([3000, mil_thrust, ab_thrust])
        ff_points = np.array([2000, mil_ff, ab_ff])

        thrust = float(np.interp(rpm, rpm_points, thrust_points))
        ff = float(np.interp(rpm, rpm_points, ff_points))

        return {"Thrust": thrust, "RPM": rpm, "FuelFlow": ff}
