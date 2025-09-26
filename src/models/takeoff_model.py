# Takeoff Model for F-14 Performance Toolkit (Refined)
# Computes takeoff performance with NATOPS-based data, thrust logic,
# flap auto-select, OEI and all-engines climb validation, and mission-card outputs.

import numpy as np
import pandas as pd
from src.models.engine_model import EngineModel
from src.models.f14_aero import AeroModel
from src.utils.data_loaders import resolve_data_path, load_is_csv


class TakeoffModel:
    def __init__(self):
        self.engine = EngineModel()
        self.aero = AeroModel()
        self.data = self._load_takeoff_data()

    def _load_takeoff_data(self):
        """Load NATOPS takeoff performance data."""
        csv_path = resolve_data_path("f14_takeoff_natops.csv")
        df = load_is_csv(csv_path)
        if df is not None and not df.empty:
            return df
        else:
            # Fallback dataset (simplified approximations)
            return pd.DataFrame({
                "Weight_lbs": [55000, 60000, 65000, 70000, 72000],
                "V1": [125, 130, 135, 140, 145],
                "Vr": [130, 135, 140, 145, 150],
                "V2": [140, 145, 150, 155, 160],
                "Vfs": [170, 175, 180, 185, 190],
                "ClimbGradient_ftnm": [320, 310, 300, 280, 260],
            })

    def _interpolate(self, weight, col):
        """Interpolate NATOPS values based on takeoff weight."""
        df = self.data
        if weight <= df["Weight_lbs"].min():
            return df[col].iloc[0]
        if weight >= df["Weight_lbs"].max():
            return df[col].iloc[-1]
        return np.interp(weight, df["Weight_lbs"], df[col])

    def compute_takeoff(self, weight_lbs, flap_setting="AUTO", thrust_mode="AUTO"):
        """Compute takeoff V-speeds, thrust, and climb gradients."""

        # --- Flap Selection Logic ---
        if flap_setting == "AUTO":
            if weight_lbs > 68000:
                flap_setting = "FULL"
            elif weight_lbs > 62000:
                flap_setting = "MANEUVER"
            else:
                flap_setting = "UP"

        # --- Thrust Logic ---
        thrust_used, rpm, ff_per_engine = self._determine_thrust(weight_lbs, thrust_mode)

        # --- Speeds ---
        v1 = self._interpolate(weight_lbs, "V1")
        vr = self._interpolate(weight_lbs, "Vr")
        v2 = self._interpolate(weight_lbs, "V2")
        vfs = self._interpolate(weight_lbs, "Vfs")

        # --- Climb Gradients ---
        climb_grad_all_eng = self._interpolate(weight_lbs, "ClimbGradient_ftnm")
        climb_grad_oei = climb_grad_all_eng * 0.55  # conservative OEI scaling

        climb_status, thrust_used = self._validate_gradients(
            climb_grad_all_eng, climb_grad_oei, thrust_used, thrust_mode, weight_lbs
        )

        # --- Trim Guidance ---
        trim_guidance = f"Trim for climb speed ({int(v2 + 15)} KCAS)"

        return {
            "Weight_lbs": weight_lbs,
            "Flaps": flap_setting,
            "ThrustType": thrust_used,
            "TakeoffRPM": int(rpm),
            "FuelFlow_pph_per_engine": int(ff_per_engine),
            "V1": int(v1),
            "Vr": int(vr),
            "V2": int(v2),
            "Vfs": int(vfs),
            "ClimbGradient_AllEng_ftnm": round(climb_grad_all_eng, 1),
            "ClimbGradient_OEI_ftnm": round(climb_grad_oei, 1),
            "ClimbStatus": climb_status,
            "Trim": trim_guidance,
        }

    def _determine_thrust(self, weight, thrust_mode):
        """Select thrust setting (MIL, AB, REDUCED)."""
        if thrust_mode.upper() == "AUTO":
            if weight > 68000:
                thrust_mode = "AFTERBURNER"
            else:
                thrust_mode = "MILITARY"

        if thrust_mode.upper().startswith("REDUCED"):
            # Extract percent RPM from input
            try:
                percent = int(thrust_mode.split("(")[1].split("%")[0])
            except Exception:
                percent = 90
            rpm = self.engine.mil_rpm * (percent / 100)
            ff = self.engine.estimate_ff(rpm)
            return f"REDUCED ({percent}%)", rpm, ff

        elif thrust_mode.upper() == "AFTERBURNER":
            rpm = self.engine.ab_rpm
            ff = self.engine.estimate_ff(rpm)
            return "AFTERBURNER", rpm, ff

        else:
            rpm = self.engine.mil_rpm
            ff = self.engine.estimate_ff(rpm)
            return "MILITARY", rpm, ff

    def _validate_gradients(self, climb_all, climb_oei, thrust_used, thrust_mode, weight):
        """Check climb gradients and auto-escalate thrust if required."""
        status = "NORMAL"

        if climb_all < 300:
            if thrust_mode.upper() != "AFTERBURNER":
                # escalate thrust
                thrust_used, rpm, ff = self._determine_thrust(weight, "AFTERBURNER")
                status = "AUTO-ESCALATED TO AB"
            elif climb_all < 200:
                status = "WARNING: <200 ft/nm, not acceptable"
            else:
                status = "CAUTION: <300 ft/nm"

        if climb_oei < 200:
            status = "OEI WARNING: <200 ft/nm"

        return status, thrust_used
