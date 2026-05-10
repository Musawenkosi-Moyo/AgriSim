# Implementation Plan - Phase 1: Markov Chain Climate Engine

This phase focuses on building the foundational climate simulation engine for **AgriSim**. The engine uses a duration-dependent Markov Chain to simulate transitions between Normal, Pre-Drought, and Drought states, generating state-conditional rainfall and temperature data.

## User Review Required

> [!IMPORTANT]
> The duration-dependency logic uses a "persistence decay" model. Please review the `TransitionManager` logic if you have specific transition curves (e.g., Weibull-distributed stay times) in mind.

## Proposed Changes

### 1. Project Structure [NEW]

We will establish a modular structure to support the 6-phase build.

```text
agrisim/
├── core/
│   ├── __init__.py
│   └── climate.py       # Phase 1: Climate Engine
├── models/              # Future models (SEIR, Soil, Agent)
├── utils/
│   └── config.py        # Constants and parameters
├── tests/
│   └── test_climate.py
└── main.py              # Entry point for simulation
```

---

### 2. Climate Engine Implementation

#### [NEW] [climate.py](file:///c:/Users/Home2026/Desktop/AGROSIM/agrisim/core/climate.py)

This file will contain the core logic for the Markov Chain and the sampling engine.

**Key Classes & Functions:**

- **`ClimateState(Enum)`**: Defines `NORMAL`, `PRE_DROUGHT`, and `DROUGHT`.
- **`TransitionManager`**:
    - `get_transition_probs(current_state, duration)`: Returns a probability vector for the next state.
    - **Math**: $P(S_{t+1} = j | S_t = i, d) = T_{ij} \cdot \phi(d)$, where $\phi(d)$ is a scaling factor that reduces persistence as duration $d$ grows.
- **`ClimateGenerator`**:
    - `sample(state)`: Samples Rainfall from a **Gamma Distribution** and Temperature from a **Normal Distribution**.
    - **Equations**:
        - $Rain \sim \Gamma(k_{state}, \theta_{state})$
        - $Temp \sim \mathcal{N}(\mu_{state}, \sigma_{state})$
- **`ClimateEngine`**:
    - `run_simulation(steps)`: The main loop that iterates through time, updating state and sampling variables.

---

### 3. Parameters & Constants

#### [NEW] [config.py](file:///c:/Users/Home2026/Desktop/AGROSIM/agrisim/utils/config.py)

We will define baseline parameters here to allow easy tuning.
- Transition matrices for $d=0$.
- Decay rates for duration dependency.
- Shape/Scale parameters for Gamma rainfall.
- Mean/Std for Temperature.

---

## Drought Prediction & Farmer Interaction

### Drought Prediction Logic
The system uses a **Probabilistic Forecasting** approach rather than a single deterministic "Rain/No Rain" prediction.
1. **The Forecast Mechanism**: The `ClimateEngine` calculates the $k$-step ahead transition probability:
   $P(S_{t+k} | S_t, d_t) = T^k(d_t)$
2. **Noise and Lag**: To simulate real-world uncertainty, the Farmer Agent receives a "Noisy Forecast."
   - **Noise**: The actual probability is jittered (e.g., if the true risk is 70%, the farmer might see 60% or 80%).
   - **Lag**: The farmer receives the forecast with a delay (e.g., today's decision is based on yesterday's atmospheric data).
3. **Duration Scenario Output (Required)**: The model must provide explicit "what-if" projections for drought duration windows that matter to farm decisions.
   - **Scenario A (Short Drought)**: 3-week drought persistence.
   - **Scenario B (Extended Drought)**: 8-week drought persistence.
   - For each scenario, output:
     - expected soil moisture trajectory by week,
     - irrigation demand estimate,
     - projected stress days,
     - projected yield impact (%) relative to baseline.
   - This output is shown side-by-side so the farmer can understand consequences of delayed action.

### Farmer Inputs (Agent Configuration)
The "Farmer" (whether played by a user or an AI agent) should configure only **real-world levers** that farmers can actually control. We replace abstract inputs with concrete operational settings.

| Input Category | User Input (What Farmer Sets) | Typical Range / Units | What the Farmer Sees Before Setting |
| :--- | :--- | :--- | :--- |
| **Irrigation Start Point** | `Irrigation_Start_Moisture` (start normal irrigation when root-zone moisture drops below threshold) | 20-45% volumetric water content (VWC) | Current soil moisture by field/zone, 7-day moisture trend, forecast drought risk |
| **Irrigation Stop Point** | `Irrigation_Stop_Moisture` (stop irrigation target to avoid overwatering) | 30-55% VWC | Last irrigation response (how much moisture rose), infiltration/drainage pattern |
| **Emergency Irrigation Trigger** | `Emergency_Moisture_Level` (critical threshold for immediate irrigation) | 10-25% VWC | Plant stress alerts, heatwave warning, consecutive dry-day counter |
| **Daily Pumping Limit** | `Max_Daily_Irrigation_mm` (hard cap due to pump/energy capacity) | 2-15 mm/day | Pump capacity, available run-hours, expected evaporation demand |
| **Season Water Budget** | `Seasonal_Water_Budget_m3` (total water allowed for season) | Farm-specific, m3/season | Remaining reservoir/allocation, projected use to harvest, budget burn-down |
| **Action Lead Time** | `Irrigation_Delay_Hours` (how quickly an action can be executed) | 0-48 hours | Labor/equipment availability and queue of pending field operations |
| **Crop Stress Sensitivity** | `Crop_Stress_Sensitivity` (crop-specific tolerance profile) | low / medium / high (or 0.0-1.0) | Crop stage (vegetative/flowering/filling), expected yield penalty under stress |

### Irrigation Policy Selection (Farmer-Controlled)
The farmer should choose the irrigation policy currently used on their farm (or compare alternatives). Policies are explicit operating rules, not hidden model behavior.

| Policy Name | Policy Rule | Typical Use Case |
| :--- | :--- | :--- |
| **Conservative / Water-Saving** | Irrigate only at low moisture threshold; smaller depth per event | Severe water limits, high pumping cost |
| **Balanced Threshold** | Moderate start/stop thresholds; moderate depth | Standard operation under uncertain forecast |
| **Yield-Protect** | Earlier triggers and higher refill targets | High-value crop stages where stress is costly |
| **Emergency Pulse** | Short, frequent rescue irrigations during critical stress | Heatwaves or sudden prolonged dry period |

### Input UX Detail (for user-facing controls)
Each farmer-facing control should include:
1. **Label + Unit**: For example, "Start irrigation below (%)", never unlabeled raw variables.
2. **Suggested Default**: Pre-filled by crop type, soil type, and growth stage.
3. **Safe Operating Range**: Show agronomic min/max and warn on extreme values.
4. **Current Observed Value**: Display live field reading beside each threshold.
5. **Estimated Impact Preview**: "If applied now: +X mm water use, -Y% drought risk, +/-Z yield impact."
6. **Reason Code in Recommendations**: Explain why a suggestion appears (e.g., "3-day heat risk + low moisture in Zone B").

### Policy Recommendation Output (Required)
For each simulation window, the result layer must evaluate all selected candidate irrigation policies and recommend one to minimize yield loss under constraints.

**Minimum output fields to user:**
- `Recommended_Policy` (one of the policy names above)
- `Why_Recommended` (plain-language reason using drought risk, crop stage, and water budget)
- `Projected_Yield_Loss_%` under recommended policy
- `Projected_Yield_Loss_%` under current policy
- `Water_Use_m3` comparison (recommended vs current)
- `Confidence` (low/medium/high based on forecast uncertainty)

**Recommendation objective:**
- Primary: keep yield above crop survival floor ("yield not to die").
- Secondary: minimize water use and operational stress while respecting `Seasonal_Water_Budget_m3` and `Max_Daily_Irrigation_mm`.

---

## Mathematical Model Details

### Duration-Dependent Transitions
Instead of a fixed matrix $P$, we use:
$P(i, i)_{effective} = P(i, i)_{base} \cdot e^{-\lambda d}$
Where $\lambda$ is the "urgency" to transition out of a long-standing state. The remaining probability is redistributed to other states based on their relative weights in the base matrix.

### Rainfall Sampling
We use the **Gamma Distribution** because rainfall is non-negative and typically skewed (many small events, few large ones).
- **Normal State**: High shape ($k$), high scale ($\theta$).
- **Drought State**: Low shape, low scale (mostly zero or near-zero).

## Verification Plan

### Automated Tests
1. **Transition Integrity**: Run 10,000 steps and verify that the proportion of time spent in each state aligns with the theoretical steady-state distribution.
2. **Duration Decay**: Verify that the probability of staying in "Drought" significantly decreases after $d > \text{threshold}$.
3. **Sampling Bounds**: Ensure rainfall never drops below zero and temperature stays within realistic bounds (e.g., -10°C to 50°C).

### Manual Verification
1. **Visualization**: Generate a 3-year plot (1095 steps) showing:
    - State transitions (background shading).
    - Rainfall bars.
    - Temperature line.
2. **Dashboard Preview**: Print a summary table showing mean rainfall/temp per state to ensure the "Drought" state is actually drier/hotter than "Normal".

## Libraries to Use
- **NumPy**: Essential for vectorised transitions and random sampling.
- **SciPy**: For the `gamma` and `norm` distribution functions.
- **Pandas**: For easy data export and time-series indexing.
- **Matplotlib**: For the initial validation plots.
