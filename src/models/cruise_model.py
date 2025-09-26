import pandas as pd
import numpy as np

class CruiseModel:
    """
    F-14 Cruise Performance Model.
    Provides cruise profiles: Best Endurance, Best Range, Optimum Efficiency, Shortest Time.
    """

    def __init__(self):
        self.cruise_data = pd.read_csv("data/f14_cruise_profiles.csv")

    def _interpolate(self, df, weight, alt_ft, mach):
        """
        Helper to interpolate cruise performance by weight, altitude, Mach.
        """
        w = np.clip(weight, df["weight"].min(), df["weight"].max())
        alt = np.clip(alt_ft, df["alt_ft"].min(), df["alt_ft"].max())
        m = np.clip(mach, df["mach"].min(), df["mach"].max())

        subset = df[(df["weight"] == w) & (df["alt_ft"] == alt)]
        return np.interp(m, subset["mach"], subset.iloc[:, -1])

    def calculate_cruise(self, weight, alt_ft, mach):
        """
        Calculate cruise profiles for different optimization strategies.
        """
        profiles = {}

        # Best Endurance
        endurance_speed = 250  # KCAS placeholder
        endurance_ff = 6000    # pph/engine placeholder
        endurance_time = 2.5   # hr endurance at this setting
        profiles["best_endurance"] = {
            "speed_kcas": endurance_speed,
            "mach": 0.55,
            "fuel_flow_pph_per_engine": endurance_ff,
            "endurance_hr": endurance_time,
            "range_nm": endurance_time * endurance_speed
        }

        # Best Range
        range_speed = 350
        range_ff = 6500
        range_time = 2.0
        profiles["best_range"] = {
            "speed_kcas": range_speed,
            "mach": 0.8,
            "fuel_flow_pph_per_engine": range_ff,
            "endurance_hr": range_time,
            "range_nm": range_time * range_speed
        }

        # Optimum Efficiency
        opt_speed = 300
        opt_ff = 6200
        opt_time = 2.2
        profiles["optimum_efficiency"] = {
            "speed_kcas": opt_speed,
            "mach": 0.7,
            "fuel_flow_pph_per_engine": opt_ff,
            "endurance_hr": opt_time,
            "range_nm": opt_time * opt_speed
        }

        # Shortest Time
        fast_speed = 450
        fast_ff = 9000
        fast_time = 1.5
        profiles["shortest_time"] = {
            "speed_kcas": fast_speed,
            "mach": 0.95,
            "fuel_flow_pph_per_engine": fast_ff,
            "endurance_hr": fast_time,
            "range_nm": fast_time * fast_speed
        }

        # Standard waypoint evaluation (200 nm)
        waypoint_nm = 200
        for key, prof in profiles.items():
            hours = waypoint_nm / prof["speed_kcas"]
            prof["fuel_used_lb"] = prof["fuel_flow_pph_per_engine"] * 2 * hours
            prof["fob_at_wp_lb"] = weight - prof["fuel_used_lb"]

        return {
            "weight": weight,
            "alt_ft": alt_ft,
            "mach": mach,
            "profiles": profiles
        }
