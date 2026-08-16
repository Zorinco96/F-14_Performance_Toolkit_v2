from src.f14perf.takeoff import AutoTakeoffSelector, TakeoffModel
from src.f14perf.types import Environment, Runway, TakeoffInputs


def baseline():
    env = Environment(field_elevation_ft=0, oat_c=15, qnh_inhg=29.92)
    rwy = Runway(heading_deg=0, tora_ft=8000, toda_ft=8000, asda_ft=8000, elevation_ft=0)
    return TakeoffInputs(65000, env, rwy)


def test_legacy_baseline_table_points(data_dir):
    model = TakeoffModel(data_dir)
    up, _ = model._mil_table("UP", 65000, 0, 15)
    full, _ = model._mil_table("FULL", 65000, 0, 15)
    assert up["vr_kt"] == 159
    assert up["asd_ft"] == 2460
    assert up["agd_ft"] == 2900
    assert full["vr_kt"] == 140
    assert full["asd_ft"] == 2168
    assert full["agd_ft"] == 2550


def test_maneuver_calibration_anchor(data_dir):
    model = TakeoffModel(data_dir)
    man, prov = model._mil_table("MANEUVER", 65000, 0, 15)
    assert man["vr_kt"] == 146
    assert round(man["asd_ft"]) == 2583
    assert round(man["agd_ft"]) == 2456
    assert prov.method.value == "CALIBRATED"


def test_auto_uses_no_afterburner_and_respects_floor(data_dir):
    result = AutoTakeoffSelector(data_dir).select(baseline())
    assert result.flaps in {"UP", "MANEUVER", "FULL"}
    floors = {"UP": 85, "MANEUVER": 90, "FULL": 98}
    assert result.rpm_pct >= floors[result.flaps]
    assert result.rpm_pct <= 100


def test_balanced_v1_below_vr(data_dir):
    result = TakeoffModel(data_dir).calculate(baseline(), "UP", 100)
    assert result.v1_kt < result.vr_kt
    assert result.v1_kt >= 0.84 * result.vr_kt - 1
