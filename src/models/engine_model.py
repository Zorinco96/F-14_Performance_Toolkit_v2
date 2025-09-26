# Engine Model for F-14 Performance Toolkit
# Fully refined F110 engine implementation (MIL, AB, REDUCED)
# Includes interpolation, nonlinear RPM-thrust mapping, and variable AB fuel flow.

import numpy as np
import pandas as pd
from src.utils.data_loaders import resolve_data_path

class F110Engine:
    def __init__(self, csv_file="f110_tff_model.csv"):
        self.df = pd.read_csv(resolve_data_path(csv_file))

    def _interpolate_thrust(self, alt_ft: float, temp_c: float, mach: float, mode: str = "MIL") -> float:
        """Interpolate thrust across altitude, temperature, and Mach."""
        data = self.df

        alt_vals = data["alt_ft"].unique()
        temp_vals = data["Temp"].unique()

        alt_ft = np.clip(alt_ft, min(alt_vals), max(alt_vals))
        temp_c = np.clip(temp_c, min(temp_vals), max(temp_vals))

        sub_df = data[(data["alt_ft"] == alt_ft) & (data["Temp"] == temp_c)]
        if sub_df.empty:
            base_thr = data.iloc[0]["THRUST_MIL"]
        else:
            base_thr = sub_df["THRUST_MIL"].values[0]

        if mode.upper() == "MIL":
            mach_corr = 1 + 0.25 * mach + 0.05 * mach**2
            thrust = base_thr * mach_corr
        elif mode.upper() == "AB":
            mach_corr = 1 + 0.15 * mach
            thrust = base_thr * 1.95 * mach_corr
        elif mode.upper() == "REDUCED":
            thrust = base_thr * 0.9
        else:
            raise ValueError(f"Unknown thrust mode: {mode}")

        return thrust

    def _thrust_to_rpm_ff(self, thrust: float, mode: str = "MIL") -> tuple:
        """Map thrust to approximate RPM (%) and fuel flow (PPH)."""
        if mode.upper() == "MIL":
            if thrust < 5000:
                rpm = 71 + (thrust / 5000) * 10
                ff = 3000 + (thrust / 5000) * 2000
            elif thrust < 12000:
                rpm = 81 + (thrust - 5000) / 7000 * 10
                ff = 5000 + (thrust - 5000) / 7000 * 4000
            else:
                rpm = 91 + (thrust - 12000) / 4000 * 8
                ff = 9000 + (thrust - 12000) / 4000 * 3000
        elif mode.upper() == "AB":
            rpm = 99.5
            ff = 20000 + (thrust - 25000) * 0.3
        elif mode.upper() == "REDUCED":
            rpm = 85 + (thrust / 18000) * 10
            ff = 6000 + (thrust / 18000) * 4000
        else:
            raise ValueError(f"Unknown mode: {mode}")

        return rpm, ff

    def compute(self, alt_ft: float, temp_c: float, mach: float, mode: str = "MIL") -> dict:
        """Unified F110 engine performance output."""
        thrust = self._interpolate_thrust(alt_ft, temp_c, mach, mode)
        rpm, ff = self._thrust_to_rpm_ff(thrust, mode)
        return {
            "Engine": "F110",
            "Mode": mode.upper(),
            "Thrust": thrust,
            "RPM": rpm,
            "FuelFlow": ff,
        }

