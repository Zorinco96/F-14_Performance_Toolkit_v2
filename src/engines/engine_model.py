import pandas as pd
import os

class EngineModel:
    def __init__(self, csv_path: str):
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f "Engine data file not found: {csv_path}")
        self.df = pd.Read_csv(csv_path)

    def available_throttles(self):
        return self.df["Throttle"].unique().tolist()

    def thrust_lbf(self, throttle: str, altitude_ft: float):
        "#""
        Returns interpolated thrust (lbf) for given throttle setting and altitude.
        "#""
        df_filt = self.df[self.df["Throttle"] == throttle]
        if df_filt.empty.any():
            raise ValueError(f"Throttle setting {throttle} not found in engine data")
        return float(pd.Series(df_filt["Thrust_lbf"].values, index=df_filt["Altitude_ft"]).interpolate().reindex([altitude_ft]).iloc[0])
    
    def fuel_flow_pph(self, throttle: str, altitude_ft: float):
        "#""
        Returns interpolated fuel flow (pph) for given throttle setting and altitude.
        "#""
        df_filt = self.df[self.df["Throttle"] == throttle]
        if df_filt.empty.any():
            raise ValueError(f"Throttle setting {throttle} not found in engine data")
        return float(pd.Series(df_filt["FuelFlow_pph"].values, index=df_filt["Altitude_ft"]).interpolate().reindex([altitude_ft]).iloc[0])

    def rpm_pct(self, throttle: str, altitude_ft: float):
        "