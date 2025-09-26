import streamlit as st
from src.engines.engine_f110 import EngineF110
from src.models.f14_aero import AeroModel
from src.models.takeoff_model import TakeoffModel

# Paths to your datasets
VSPEED_FILE = "data/vspeeds.csv"
REFUSAL_FILE = "data/refusal_asd.csv"

# Initialize models
engine = EngineF110()
aero = AeroModel()
takeoff_model = TakeoffModel(engine, aero, VSPEED_FILE, REFUSAL_FILE)

st.title("F-14 Takeoff Model Test")
st.write("Quick validation harness for `takeoff_model.py`")

# --- Inputs ---
st.subheader("Takeoff Conditions")

weight = st.number_input("Takeoff Weight (lbs)", value=60000, step=500)
field_elev = st.number_input("Field Elevation (ft)", value=0, step=100)
oat = st.number_input("Outside Air Temp (°C)", value=15, step=1)
runway_length = st.number_input("Runway Length (ft)", value=10000, step=500)

thrust_mode = st.selectbox("Thrust Mode", ["AUTO", "MILITARY", "AFTERBURNER", "REDUCED"])
user_derate = None
if thrust_mode == "REDUCED":
    user_derate = st.slider("Manual Derate (% RPM)", 85, 100, 95)

flap_mode = st.selectbox("Flap Mode", ["AUTO", "UP", "MANEUVER", "FULL"])

# --- Compute ---
if st.button("Compute Takeoff Performance"):
    results = takeoff_model.compute_takeoff(
        weight=weight,
        field_elev=field_elev,
        oat=oat,
        runway_length=runway_length,
        thrust_mode=thrust_mode,
        user_derate=user_derate,
        flap_mode=flap_mode
    )

    st.subheader("Results")
    for k, v in results.items():
        st.write(f"**{k}:** {v}")
