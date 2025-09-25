import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def resolve_data_path(filename):
    return os.path.join(BASE_DIR, "data", os.path.basename(filename))

def load_takeoff_data():
    path = resolve_data_path("takeoff_data_expanded.csv")
    if os.path.exists(path):
        return pd.read_csv(path).to_dict(orient="records")[0]
    return {}

def load_v_speeds():
    path = resolve_data_path("v_speeds.csv")
    if os.path.exists(path):
        return pd.read_csv(path).to_dict(orient="records")[0]
    return {}

def load_asd_data():
    path = resolve_data_path("refusal_asd.csv")
    if os.path.exists(path):
        return pd.read_csv(path).to_dict(orient="records")[0]
    return {}
