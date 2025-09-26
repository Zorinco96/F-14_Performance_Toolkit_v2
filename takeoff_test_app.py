import streamlit as st
from src.models.takeoff_model import TakeoffModel
from src.models.landing_model import LandingModel
from src.models.cruise_model import CruiseModel
from src.engines.engine_f110 import F110Deck  # ✅ corrected import

st.title("F-14 Performance Toolkit – Test Harness")

# --- Takeoff Test ---
st.header("Takeoff Performance Test")
try:
    to_model = TakeoffModel()
    to_result = to_model.compute_takeoff(
        weight_lbs=65000, flap_setting="AUTO", thrust_mode="AUTO"
    )
    st.json(to_result)
except Exception as e:
    st.error(f"Takeoff test failed: {e}")

# --- Landing Test ---
st.header("Landing Performance Test")
try:
    ldg_model = LandingModel()
    ldg_result = ldg_model.compute_landing(
        weight_lbs=56000, flap_setting="FULL", runway_condition="WET"
    )
    st.json(ldg_result)
except Exception as e:
    st.error(f"Landing test failed: {e}")

# --- Cruise Test ---
st.header("Cruise Performance Test")
try:
    crz_model = CruiseModel()
    crz_result = crz_model.compute_cruise(
        weight_lbs=60000, altitude_ft=25000, profile="Best Range"
    )
    st.json(crz_result)
except Exception as e:
    st.error(f"Cruise test failed: {e}")

# --- Engine Deck Test ---
st.header("F110 Engine Deck Test")
try:
    f110 = F110Deck()
    thrust = f110.thrust_lbf(alt_ft=0, mach=0.0, power="MIL")
    st.write(f"F110 MIL thrust at SL, Mach 0: {thrust:.0f} lbf")
    thrust_ab = f110.thrust_lbf(alt_ft=0, mach=0.0, power="MAX AB")
    st.write(f"F110 MAX AB thrust at SL, Mach 0: {thrust_ab:.0f} lbf")
except Exception as e:
    st.error(f"F110 Engine Deck test failed: {e}")
