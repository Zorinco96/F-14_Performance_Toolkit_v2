# Cruise Model for F-14 Performance Toolkit (Refined)
# Computes cruise profiles using NATOPS-derived data with interpolation.
# Supports Economy, Interceptor, Best Range, Best Endurance, and Shortest Time profiles.

import numpy as np
import pandas as pd
from src.utils.data_loaders import resolve_data_path, load_is_csv


class CruiseModel:
    def __init__(self):
        self.data = self._load_natops_data()

    def _load_natops_data(self):
        """Load NATOPS cruise data if available, otherwise fallback."""
        csv_path = resolve_data_path("f14_cruise_natops.csv")
        df = load_is_csv(csv_path)
        if df is not None and not df.empty:
            return df
        else:
            # Fallback dataset if CSV not found (simplified approximate values)
            return pd.DataFrame({
                "Altitude_ft": [20000, 25000, 30000, 35000],
                "Economy_Mach": [0.72, 0.75, 0.78, 0.80],
                "Interceptor_Mach": [0.85, 0.90, 0.95, 1.00],
                "BestRange_Mach": [0.76, 0.78, 0.80, 0.82],
                "BestEndurance_Mach": [0.70, 0.72, 0.74, 0.76],
                "ShortestTime_Mach": [0.90, 0.95, 1.00, 1.05],
                "FuelFlow_lbhr_per_engine": [7500, 7000, 6800, 6600],
                "TAS_kts": [420, 450, 480, 510],
            })

    def _interpolate(self, alt_ft, col):
        """Linearly interpolate between available altitudes."""
        df = self.data
        if alt_ft <= df["Altitude_ft"].min():
            return df[col].iloc[0]
        if alt_ft >= df["Altitude_ft"].max():
            return df[col].iloc[-1]
        return np.interp(alt_ft, df["Altitude_ft"], df[col])

    def compute_profile(self, alt_ft, profile="economy"):
        """Compute cruise metrics at a given altitude and profile."""
        profile = profile.lower()
        valid_profiles = {
            "economy": "Economy_Mach",
            "interceptor": "Interceptor_Mach",
            "bestrange": "BestRange_Mach",
            "bestendurance": "BestEndurance_Mach",
            "shortesttime": "ShortestTime_Mach",
        }
        if profile not in valid_profiles:
            raise ValueError(f"Invalid profile {profile}. Choose from {list(valid_profiles.keys())}")

        # Interpolated Mach
        mach = self._interpolate(alt_ft, valid_profiles[profile])
        # Interpolated TAS
        tas = self._interpolate(alt_ft, "TAS_kts")
        # Interpolated fuel flow
        ff_per_engine = self._interpolate(alt_ft, "FuelFlow_lbhr_per_engine")
        ff_total = ff_per_engine * 2

        # Estimate endurance and range (simplified)
        endurance_hr = 10000 / ff_total  # for 10,000 lb fuel
        range_nm = tas * endurance_hr

        return {
            "Altitude_ft": alt_ft,
            "Profile": profile.capitalize(),
            "Mach": round(mach, 3),
            "TAS_kts": round(tas, 1),
            "FuelFlow_lbhr_per_engine": int(ff_per_engine),
            "FuelFlow_lbhr_total": int(ff_total),
            "Endurance_hr": round(endurance_hr, 2),
            "Range_nm": int(range_nm),
        }
