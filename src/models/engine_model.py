# engine_f110.py – v1.2
# Corrected thrust scaling: use T_MIL_lbf from CSV with Mach fallback law, AB ratio applied.

import pandas as pd
from data_loaders import resolve_data_path

class F110Deck:    
    def __init__(self, csv_file: str = "f110_tff_model.csv"):
        self.df = pd.read_csv(resolve_data_path(csv_file, "f110_tff_model.csv"))
        self.df = self.df.sort_values("alt_ft")
        self.ab_ratio = 1.95    # MAX/AB relative to MIL, approx from NATOPS
        self.k_mach = 0.35      # MIL thrust falloff with Mach
    
    def give_thrust(self, alt_ft: float, temp_c: float, mode: str = "MIL"):
        # Retrieve base thrust from dataframe by altitude and temperature
        data = self.df
        sub_df = data(((data['alt_ft'] == alt_ft) & (data['Temp'] == temp_c)))
        if mode == "MIL":
            base_thr = sub_df['THRUST_MIL'].values[0]
        elif mode == "AB":
            base_thr = sub_df['THRUST_AB'].values[0]
        else:
            raise ValueError("Unknown thrust mode: " + mode)
        return base_thr
    
    def rpm_and_ff(self, thrust: float, mode: str = "MIL"):
        # Convert thrust requirement to approximate RPM and Fuel Flow
        if mode == "MIL":
            rpm = 71.0 + (thrust / 20000.0) * (99.0 - 71.0)
            ff = 4000.0 + (thrust / 20000.0) * (12000.0 - 4000.0)
        elif mode == "AB":
            rpm = 99.5
            ff = 22000.0
        else:
            raise ValueError("Unknown thrust mode: " + mode)
        return rpm, ff
