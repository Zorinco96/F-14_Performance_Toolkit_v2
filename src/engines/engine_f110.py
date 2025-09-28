import pandas as pd
import numpy as np

class EngineF110:
    """
    F110 engine model for F-14B/D Tomcat.
    Provides thrust (lbf), fuel flow (pph), and RPM (%) across altitude/Mach.
    Supports MIL, AB, Idle, and reduced derates.
    """

    def __init__(self, csv_path="data/f110_tff_model.csv"):
        # Load dataset
        self.data = pd.read_csv(csv_path)

        # Expect columns: Altitude_ft, Mach, RPM_pct, Thrust_lbf, FuelFlow_pph
        required = {"Altitude_ft", "Mach", "RPM_pct", "Thrust_lbf", "FuelFlow_pph"}
        if not required.issubset(self.data.columns):
            raise ValueError(f"CSV must include {required}")

        # Unique sorted axes for interpolation
        self.altitudes = sorted(self.data["Altitude_ft"].unique())
        self.machs = sorted(self.data["Mach"].unique())

        # Define typical operating points
        self.idle_rpm = 71.0
        self.mil_rpm = 99.0
        self.ab_rpm = 103.0

    def _interpolate(self, altitude_ft, mach, rpm_pct):
        """
        Bilinear interpolation across altitude + Mach for thrust/fuel flow.
        """
        # Find nearest grid points
        alt_low = max([a for a in self.altitudes if a <= altitude_ft], default=min(self.altitudes))
        alt_high = min([a for a in self.altitudes if a >= altitude_ft], default=max(self.altitudes))
        mach_low = max([m for m in self.machs if m <= mach], default=min(self.machs))
        mach_high = min([m for m in self.machs if m >= mach], default=max(self.machs))

        def get_point(alt, m):
            df = self.data[(self.data["Altitude_ft"] == alt) & (self.data["Mach"] == m)]
            if df.empty:
                return None
            # Interpolate thrust + fuel flow at this RPM
            thrust = np.interp(rpm_pct, df["RPM_pct"], df["Thrust_lbf"])
            ff = np.interp(rpm_pct, df["RPM_pct"], df["FuelFlow_pph"])
            return thrust, ff

        # Corner values
        q11 = get_point(alt_low, mach_low)
        q12 = get_point(alt_low, mach_high)
        q21 = get_point(alt_high, mach_low)
        q22 = get_point(alt_high, mach_high)

        # Fallback if missing
        if None in [q11, q12, q21, q22]:
            df = self.data[(self.data["Altitude_ft"] == alt_low) & (self.data["Mach"] == mach_low)]
            thrust = np.interp(rpm_pct, df["RPM_pct"], df["Thrust_lbf"])
            ff = np.interp(rpm_pct, df["RPM_pct"], df["FuelFlow_pph"])
            return thrust, ff

        # Bilinear interpolation
        def bilinear(x, y, q11, q12, q21, q22, x1, x2, y1, y2):
            return (
                q11 * (x2 - x) * (y2 - y) +
                q21 * (x - x1) * (y2 - y) +
                q12 * (x2 - x) * (y - y1) +
                q22 * (x - x1) * (y - y1)
            ) / ((x2 - x1) * (y2 - y1))

        thrust = bilinear(mach, altitude_ft,
                          q11[0], q12[0], q21[0], q22[0],
                          mach_low, mach_high, alt_low, alt_high)
        ff = bilinear(mach, altitude_ft,
                      q11[1], q12[1], q21[1], q22[1],
                      mach_low, mach_high, alt_low, alt_high)
        return thrust, ff

    def get_performance(self, altitude_ft, mach, mode="MIL", derate_rpm=None, weight_lbs=None, distance_nm=None):
        """
        Returns thrust (lbf), RPM (%), fuel flow (pph).
        Modes: "IDLE", "MIL", "AB", "DERATE"
        """
        if mode == "IDLE":
            rpm = self.idle_rpm
        elif mode == "MIL":
            rpm = self.mil_rpm
        elif mode == "AB":
            rpm = self.ab_rpm
        elif mode == "DERATE":
            if derate_rpm is None:
                raise ValueError("Must supply derate_rpm for DERATE mode.")
            rpm = max(self.idle_rpm, min(derate_rpm, self.mil_rpm))
        else:
            raise ValueError("Mode must be IDLE, MIL, AB, or DERATE")

        thrust, ff = self._interpolate(altitude_ft, mach, rpm)

        # Climb gradient check (if weight + distance provided)
        if weight_lbs and distance_nm:
            gradient = (thrust * 2 / weight_lbs) * 6076  # ft/nm approx
            if gradient < 300:  # if below spec, bump thrust
                rpm = min(self.ab_rpm, rpm + 2)
                thrust, ff = self._interpolate(altitude_ft, mach, rpm)

        return {
            "Thrust_lbf": thrust,
            "RPM_pct": rpm,
            "FuelFlow_pph": ff
        }
