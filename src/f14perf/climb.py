from __future__ import annotations

import math
from pathlib import Path

from .aero import F14AeroModel
from .atmosphere import atmosphere, ias_to_tas_kt, isa_temperature_c, mach_from_tas
from .engine import F110Deck
from .provenance import Method, Provenance, combine
from .types import ClimbPoint


KG_M3_TO_SLUG_FT3 = 0.00194032033
KT_TO_FPS = 1.68780986


class ClimbModel:
    def __init__(self, data_dir: Path | str | None = None):
        self.engine = F110Deck(data_dir)
        self.aero = F14AeroModel()

    def point(
        self,
        weight_lb: float,
        altitude_ft: float,
        ias_kt: float,
        rpm_pct: float = 100.0,
        isa_delta_c: float = 0.0,
        drag_index: float = 0.0,
        engines: int = 2,
    ) -> ClimbPoint:
        oat = isa_temperature_c(altitude_ft) + isa_delta_c
        atm = atmosphere(altitude_ft, oat)
        tas_kt = ias_to_tas_kt(ias_kt, atm["sigma"])
        mach = mach_from_tas(tas_kt, atm["speed_of_sound_kt"])
        eng = self.engine.total(
            altitude_ft, mach, mode="MIL", rpm_pct=rpm_pct, oat_c=oat, engines=engines
        )
        rho_slug = atm["rho_kg_m3"] * KG_M3_TO_SLUG_FT3
        aero = self.aero.point(
            weight_lb,
            rho_slug,
            tas_kt * KT_TO_FPS,
            mach,
            config="CLEAN",
            load_factor=1.0,
            drag_index=drag_index,
        )
        excess = eng.thrust_lbf_per_engine - aero.drag_lbf
        gradient = max(-3000.0, excess / max(1.0, weight_lb) * 6076.12)
        roc = gradient * tas_kt / 60.0
        prov = Provenance(
            Method.ESTIMATED,
            "F110 deck + low-order excess-thrust climb model",
            f"{engines} engine(s), {ias_kt:.0f} KIAS, {rpm_pct:.0f}% RPM, DI {drag_index:.0f}",
            "Medium for trend comparison; not a released F-14B climb chart",
        )
        return ClimbPoint(
            altitude_ft=round(altitude_ft),
            ias_kt=round(ias_kt, 1),
            tas_kt=round(tas_kt, 1),
            rpm_pct=round(rpm_pct, 1),
            roc_fpm=round(roc),
            gradient_ft_nm=round(gradient),
            fuel_flow_pph_total=round(eng.fuel_flow_pph_per_engine),
            provenance=prov,
        )

    def recommend_schedule(
        self,
        weight_lb: float,
        isa_delta_c: float = 0.0,
        drag_index: float = 0.0,
        target_gradient_ft_nm: float = 300.0,
        start_alt_ft: int = 1000,
        end_alt_ft: int = 10000,
    ) -> list[ClimbPoint]:
        schedule: list[ClimbPoint] = []
        speeds = list(range(190, 251, 10))
        for altitude in range(start_alt_ft, end_alt_ft + 1, 1000):
            chosen = None
            for rpm in range(85, 101):
                candidates = [
                    self.point(weight_lb, altitude, ias, rpm, isa_delta_c, drag_index)
                    for ias in speeds
                ]
                feasible = [p for p in candidates if p.gradient_ft_nm >= target_gradient_ft_nm and p.roc_fpm > 0]
                if feasible:
                    chosen = min(
                        feasible,
                        key=lambda p: (p.fuel_flow_pph_total / max(1.0, p.roc_fpm), p.ias_kt),
                    )
                    break
            if chosen is None:
                candidates = [
                    self.point(weight_lb, altitude, ias, 100.0, isa_delta_c, drag_index)
                    for ias in speeds
                ]
                chosen = max(candidates, key=lambda p: p.roc_fpm)
            schedule.append(chosen)
        return schedule
