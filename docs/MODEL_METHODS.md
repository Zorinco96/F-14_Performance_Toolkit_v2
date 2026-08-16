# V3 Model Methods

## Takeoff

### MIL reference

UP and FULL configurations use the legacy `f14_perf.csv` MIL grid when available.

The independent variables are:

- gross weight
- pressure altitude
- OAT

The outputs are:

- Vs reference
- V1 reference
- Vr
- V2
- ASD
- AGD

### Maneuver flaps

Maneuver flaps use the established 65,000 lb DCS anchor and inherit environmental scaling from the UP table.

### Reduced thrust

The F110 deck supplies MIL and idle endpoints. Reduced dry thrust uses a nonlinear RPM interpolation between those endpoints. Takeoff distance increases with reduced thrust using an empirical acceleration exponent.

This is a calibration model. It is not a claim that engine thrust is a direct algebraic function of indicated RPM in the real aircraft.

### Balanced-field-style V1

The source grid contains a reference V1, ASD, and AGD, but the project does not have a controlled engine-cut sweep for every configuration.

V3 therefore searches candidate V1 in 0.5 kt increments below Vr and minimizes the difference between:

- reject distance, scaled primarily with kinetic energy
- continue distance, adjusted with an explicit estimated OEI sensitivity to engine-failure speed

The UI shows both the table reference V1 and the v3 balanced-field-style V1.

This is intentionally marked ESTIMATED.

### Runway

The default planning factor is 1.10.

V3 separately compares:

- factored ASD to ASDA
- factored AGD to TODA

Wind is applied using ground-speed energy scaling. Slope and wet-runway effects are engineering corrections and are labeled accordingly.

### AUTO

Configuration priority:

1. UP
2. MANEUVER
3. FULL

RPM is searched upward from:

- UP 85%
- MANEUVER 90%
- FULL 98%

The first candidate satisfying runway limits and the AEO climb gate is selected.

Afterburner is never selected by AUTO.

## Initial climb gate

The takeoff decision logic retains the project’s calibrated initial-climb model rather than substituting the general excess-thrust climb model. This keeps the AUTO gate tied to observed DCS behavior.

Default AEO gate: 300 ft/NM.

OEI climb is shown separately as an advisory estimate.

## Climb schedule

From 1,000 to 10,000 ft, the climb model searches:

- 190 to 250 KIAS
- 85 to 100% RPM

It chooses the lowest RPM that satisfies the requested gradient, then selects the candidate with favorable fuel-per-foot climbed.

The model uses:

- F110 legacy engine deck
- ISA atmosphere with ISA deviation
- low-order clean drag polar

The schedule is an ESTIMATED DCS planning product.

## Landing

Landing ground roll uses direct/interpolated values from `f14_landing_natops_full.csv`.

On-speed AOA is 15 units per current Heatblur cockpit documentation. On-speed IAS is an explicit weight-scaled estimate and is labeled as such.

## Cruise

Optimum altitude and Mach use the legacy cruise table.

The low-order aerodynamic model determines required thrust at the table condition. The F110 deck is then searched for the lowest modeled dry RPM that meets drag. Fuel flow, specific range, and endurance are therefore estimates.

## Energy maneuverability

The energy model calculates:

- specific excess power
- lift-limited instantaneous G
- instantaneous turn rate/radius
- thrust-limited sustained G
- sustained turn rate/radius

The user supplies a planning G limit. V3 does not assert that default as a structural NATOPS limit.

## Fuel

Mission fuel is phase-based:

- taxi/takeoff allowance
- integrated 1,000–10,000 ft climb schedule
- estimated continuation climb to optimum cruise altitude
- cruise fuel from modeled fuel flow and route distance
- descent/approach allowance

The result is a planning estimate, not an F-14 fuel-planning chart replacement.
