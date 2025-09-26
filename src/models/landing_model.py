# Landing Model for F-14 Performance Toolkit (Enhanced)
# Computes landing performance with flap-specific V-speeds, 
# pressure altitude corrections, wet/contaminated runway factors, 
# and OEI go-around integration with climb_model.

import numpy as np
from src.models.climb_model import ClimbModel

class LandingModel:
    def __init__(self):
        # NATOPS baseline V-speeds (approx values at 54,000 lbs)
        self.Vref_base = {"UP": 170, "MAN": 150, "FULL": 140}
        self.Vac_base = {"UP": 150, "MAN": 135, "FULL": 120}
        self.Vfs_base = {"UP": 160, "MAN": 145, "FULL": 135}
        self.base_weight = 54000  # lbs reference

        self.ldg_safety_factor = 1.1

    def _weight_adjusted_speed(self, base_speed, weight):
        return base_speed * np.sqrt(weight / self.base_weight)

    def _altitude_correction(self, alt_ft):
        """Landing distance increases ~7% per 1,000 ft elevation."""
        return 1 + 0.07 * (alt_ft / 1000.0)

    def calc_landing(self, weight, alt_ft, flap_setting, runway_length=10000,
                     runway_condition="DRY", headwind=0, tailwind=0):
        flap = flap_setting.upper()
        if flap not in self.Vref_base:
            raise ValueError(f"Invalid flap setting {flap}. Must be UP, MAN, or FULL.")

        # Adjust speeds for weight and flap
        Vref = self._weight_adjusted_speed(self.Vref_base[flap], weight)
        Vac = self._weight_adjusted_speed(self.Vac_base[flap], weight)
        Vfs = self._weight_adjusted_speed(self.Vfs_base[flap], weight)

        # Baseline landing distance scaling with weight
        ldr = 8000 * (weight / self.base_weight)

        # Apply safety factor and altitude correction
        ldr *= self.ldg_safety_factor
        ldr *= self._altitude_correction(alt_ft)

        # Adjust for runway surface
        if runway_condition.upper() == "WET":
            ldr *= 1.15
        elif runway_condition.upper() == "CONTAMINATED":
            ldr *= 1.3

        # Adjust for wind
        ldr *= (1 - 0.05 * (headwind / 10.0))
        ldr *= (1 + 0.1 * (tailwind / 10.0))

        # OEI go-around using climb_model
        climb = ClimbModel()
        oei_profile = climb.compute_profiles(weight, 15, alt_max=3000)
        oei_grad = oei_profile[0]["OEIGradient"]

        go_around = {
            "Speed": 200,
            "ROC": oei_grad * (200 / 60),  # convert ft/nm gradient to fpm approx
            "ThrustMode": "MIL",
            "OEIGradient": oei_grad
        }

        warnings = []
        if ldr > runway_length:
            warnings.append("Landing distance exceeds available runway!")
        if oei_grad < 200:
            warnings.append("OEI climb gradient below 200 ft/nm!")

        return {
            "Vref": round(Vref, 1),
            "Vac": round(Vac, 1),
            "Vfs": round(Vfs, 1),
            "LandingDistance": int(ldr),
            "RunwayLength": runway_length,
            "Flaps": flap,
            "RunwayCondition": runway_condition.upper(),
            "Headwind": headwind,
            "Tailwind": tailwind,
            "GoAround": go_around,
            "Warnings": warnings
        }
