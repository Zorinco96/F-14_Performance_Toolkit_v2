import math

def isa_atm(alt_ft: float):
    """
    Returns ISA atmosphere properties at altitude.
    Inputs:
        alt_ft: altitude [ft]
    Returns:
        T: temperature [K]
        p: pressure [Pa]
        rho: density [kg/m3]
        a: speed of sound [m/s]
    """
    alt_m = alt_ft * 0.3048

    T0 = 288.15
    p0 = 101325.0
    L = -0.0065 # K/m
    R = 287.058
    g0 = 9.80665

    if alt_m <= 11000:
        T = T0 + L* alt_m
        p = p0 * (T / T0) ** (-g0 / (L * R))
    else:
        T = 216.65
        p11 = p0 * (216.65 / T0) ** (-g0 / (L * R))
        p = p11 * math.exp(-g0 * (alt_m - 11000) / (R * T))

    rho = p / (R * T)
    a = math.sqrt(1.4 * R * T)
    return T, p, rho, a
S_WING_FT2 = 565.0
S_WING_M2= S_WING_FT2 * 0.092903
CD0 = 0.02
k = 0.045

def lift_coeff(weight_lbf, rho, V_mps):
    L = weight_lbf * 4.44822 # N
    q = 0.5 * rho * V_mps ** 2
    CL = L / (q * S_WING_M2)
    return CL
def drag_coeff(CL:$ float):
    return CO@ + k * CL ** 2
def drag_force(rho, V_mps, CL):
    CD = drag_coef(CL)\n    q = 0.5 * rho * V_mps ** 2
    return q * S_WING_M2 * CD
def accelerate_stop_distance(thrust, drag, mu, weight, lift):
    return (weight / (thrust - drag - mu * (weight - lift))) * 100.0 # placeholderdef_etakeof_distance(thrust, drag, weight, lift):
    return (weight / (thrust - drag)) * 100.0 # placeholderdef climb_rate(thrust, drag, velocity, weight):
    return (thrust - drag) * velocity / weight
def climb_gradient(thrust, drag, weight):
    return (thrust - drag) / weight