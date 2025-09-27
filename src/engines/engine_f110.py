import pandas as pd
import numpy as np


class F110EngineModel:
    """
    General Electric F110 Engine Model for the F-14B/D Tomcat.

    Uses NATOPS-derived performance tables to interpolate thrust,
    RPM, and fuel flow across altitude, Mach, and thrust setting.
    """

    def __init__(self, dataset: pd.DataFrame):
        """
        Initialize the model with a dataset.

        dataset: DataFrame with columns:
        - ThrustType (IDLE, MIL, AB)
        - Altitude_ft
        - Mach
        - RPM_pct
        - Thrust_lbf
        - FuelFlow_pph
        """
        self.data = dataset

    def _interpolate(self, thrust_type: str, altitude_ft: float, mach: float):
        """
        Bilinear interpolation of thrust data across altitude and Mach.
        Falls back to 1D or direct match if one axis is fixed.
        """
        df = self.data[self.data["ThrustType"] == thrust_type]

        if df.empty:
            raise ValueError(f"No data available for thrust type {thrust_type}")

        # Unique sorted breakpoints
        machs = np.sort(df["Mach"].unique())
        alts = np.sort(df["Altitude_ft"].unique())

        # Bounds
        mach_low, mach_high = machs[machs <= mach].max(), machs[machs >= mach].min()
        alt_low, alt_high = alts[alts <= altitude_ft].max(), alts[alts >= altitude_ft].min()

        # Direct match
        if mach_low == mach_high and alt_low == alt_high:
            row = df[(df["Mach"] == mach_low) & (df["Altitude_ft"] == alt_low)].iloc[0]
            return row["Thrust_lbf"], row["RPM_pct"], row["FuelFlow_pph"]

        # 1D along altitude
        if mach_low == mach_high:
            rows = df[df["Mach"] == mach_low]
            return (
                np.interp(altitude_ft, rows["Altitude_ft"], rows["Thrust_lbf"]),
                np.interp(altitude_ft, rows["Altitude_ft"], rows["RPM_pct"]),
                np.interp(altitude_ft, rows["Altitude_ft"], rows["FuelFlow_pph"]),
            )

        # 1D along Mach
        if alt_low == alt_high:
            rows = df[df["Altitude_ft"] == alt_low]
            return (
                np.interp(mach, rows["Mach"], rows["Thrust_lbf"]),
                np.interp(mach, rows["Mach"], rows["RPM_pct"]),
                np.interp(mach, rows["Mach"], rows["FuelFlow_pph"]),
            )

        # 2D bilinear interpolation
        q11 = df[(df["Mach"] == mach_low) & (df["Altitude_ft"] == alt_low)].iloc[0]
        q12 = df[(df["Mach"] == mach_low) & (df["Altitude_ft"] == alt_high)].iloc[0]
        q21 = df[(df["Mach"] == mach_high) & (df["Altitude_ft"] == alt_low)].iloc[0]
        q22 = df[(df["Mach"] == mach_high) & (df["Altitude_ft"] == alt_high)].iloc[0]

        def bilinear(val11, val12, val21, val22):
            return (
                val11 * (alt_high - altitude_ft) * (mach_high - mach)
                + val21 * (alt_high - altitude_ft) * (mach - mach_low)
                + val12 * (altitude_ft - alt_low) * (mach_high - mach)
                + val22 * (altitude_ft - alt_low) * (mach - mach_low)
            ) / ((alt_high - alt_low) * (mach_high - mach_low))

        thrust = bilinear(q11["Thrust_lbf"], q12["Thrust_lbf"], q21["Thrust_lbf"], q22["Thrust_lbf"])
        rpm = bilinear(q11["RPM_pct"], q12["RPM_pct"], q21["RPM_pct"], q22["RPM_pct"])
        ff = bilinear(q11["FuelFlow_pph"], q12["FuelFlow_pph"], q21["FuelFlow_pph"], q22["FuelFlow_pph"])
        return thrust, rpm, ff

    def compute(self, thrust_type: str, altitude_ft: float, mach: float, derate: float = None):
        """
        Compute thrust, RPM, and fuel flow for a given condition.

        thrust_type: "IDLE", "MIL", "AB", or "DERATE"
        altitude_ft: altitude in feet
        mach: flight Mach number
        derate: optional RPM percentage for DERATE
        """
        # Treat DERATE as scaled MIL
        if thrust_type == "DERATE":
            thrust, rpm, ff = self._interpolate("MIL", altitude_ft, mach)
            if derate:
                thrust *= derate / 99.0  # scale relative to MIL rpm=99%
                ff *= derate / 99.0
                rpm = derate
            return {"Thrust_lbf": round(thrust, 0), "RPM_pct": round(rpm, 1), "FuelFlow_pph": round(ff, 0)}

        # Standard cases
        thrust, rpm, ff = self._interpolate(thrust_type, altitude_ft, mach)
        return {"Thrust_lbf": round(thrust, 0), "RPM_pct": round(rpm, 1), "FuelFlow_pph": round(ff, 0)}
