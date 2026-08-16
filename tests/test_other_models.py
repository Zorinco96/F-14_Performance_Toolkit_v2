from src.f14perf.climb import ClimbModel
from src.f14perf.cruise import CruiseModel
from src.f14perf.energy import EnergyModel
from src.f14perf.fuel import FuelModel
from src.f14perf.landing import LandingModel
from src.f14perf.types import Environment, Runway


def test_climb_schedule_caps_ias(data_dir):
    schedule = ClimbModel(data_dir).recommend_schedule(65000)
    assert len(schedule) == 10
    assert max(p.ias_kt for p in schedule) <= 250


def test_cruise_table_point(data_dir):
    c = CruiseModel(data_dir).optimum(65000, 0)
    assert c.optimum_altitude_ft == 33900
    assert c.optimum_mach == 0.718
    assert c.fuel_flow_pph_total > 0


def test_landing_table_point(data_dir):
    env = Environment(field_elevation_ft=0, oat_c=15, qnh_inhg=29.92)
    rwy = Runway(heading_deg=0, tora_ft=8000, toda_ft=8000, asda_ft=8000, elevation_ft=0)
    l = LandingModel(data_dir).calculate(54000, env, rwy)
    assert l.ground_roll_ft == 2800
    assert l.on_speed_aoa_units == 15


def test_energy_model_finite(data_dir):
    e = EnergyModel(data_dir).calculate(60000, 10000, 350)
    assert e.instantaneous_g >= 1
    assert e.sustained_g >= 1
    assert e.instantaneous_turn_rate_dps >= 0


def test_fuel_plan(data_dir):
    climb = ClimbModel(data_dir).recommend_schedule(65000)
    cruise = CruiseModel(data_dir).optimum(65000, 0)
    f = FuelModel().plan(16000, 100, climb, cruise, 4000, 2000)
    assert f.mission_burn_lb > 0
    assert f.landing_fuel_lb < f.starting_fuel_lb
