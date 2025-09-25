# Engine model for F-14 (F110-GE-400)

import numpy as np
from src.data_loaders import resolve_data_path

class F110Engine:
    def __init__(self, model_csv="data/f110_tff_model.csv"):
        self.model_csv = resolve_data_path(model_csv)
        # Placeholder: load model data here if needed

    def compute(self, alt_ft, oat_c, mach, thrust_mode="MIL"):
        # Placeholder NATOPS-based thrust logic
        if thrust_mode == "MIL":
            thrust = 16000
            rpm = 99
            ff = 10500
        elif thrust_mode == "AB":
            thrust = 27000
            rpm = 103
            ff = 16000
        else:
            thrust = 14000
            rpm = 95
            ff = 9000

        return {"Thrust": thrust, "RPM": rpm, "FuelFlow": ff}

    def compute_from_rpm(self, alt_ft, oat_c, mach, rpm):
        # Placeholder: map rpm to thrust/ff
        thrust = 160 * rpm
        ff = 100 * rpm
        return {"Thrust": thrust, "RPM": rpm, "FuelFlow": ff}
