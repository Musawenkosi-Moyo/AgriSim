# AgriSim: Agricultural Resilience Dashboard

AgriSim is a professional, full-stack decision-support system designed to help farmers, agronomists, and researchers predict crop yields and optimize water usage under varying drought severities. 

By combining **stochastic weather generation (Markov Chains)** with **crop-specific physiological models** and **soil-moisture drawdown simulation**, AgriSim models how four different irrigation strategies perform across short-term and extended drought horizons. The application features a high-fidelity, single-page web dashboard with an elegant dark agriculture aesthetic, glassmorphic UI elements, and interactive base64-rendered analytics.

---

## Table of Contents
1. [Key Features](#1-key-features)
2. [Project Architecture](#2-project-architecture)
3. [Mathematical & Simulation Models](#3-mathematical--simulation-models)
   - [A. Markov Chain Climate Engine](#a-markov-chain-climate-engine)
   - [B. Weather Sampling & Distribution](#b-weather-sampling--distribution)
   - [C. Soil Moisture Drawdown Model](#c-soil-moisture-drawdown-model)
   - [D. Crop Physiology & Stress Days](#d-crop-physiology--stress-days)
   - [E. Yield Loss & Harvesting Model](#e-yield-loss--harvesting-model)
   - [F. Irrigation Policy & Optimization Heuristic](#f-irrigation-policy--optimization-heuristic)
4. [Technology Stack](#4-technology-stack)
5. [Installation & Setup](#5-installation--setup)
6. [Interactive User Journey](#6-interactive-user-journey)
7. [Presentation Talking Points](#7-presentation-talking-points)

---

## 1. Key Features

- **Crop-Specific Biological Profiles:** Models physiological traits for Maize, Wheat, Sorghum, Groundnuts, and Tobacco.
- **Probabilistic Drought Modeling:** Uses Markov Chain transition matrices calibrated for Mild, Moderate, and Extreme drought scenarios.
- **Side-by-Side Scenario Horizons:** Automatically runs and compares outcomes across short-term and long-term drought horizons (e.g., 3-week vs. 8-week durations).
- **Decision-Support Recommendation Engine:** Evaluates all candidate irrigation policies to recommend the strategy that best balances maximizing yield while preventing water waste.
- **Farm-Wide Harvest Predictor:** Calculates benchmark expected yields vs. actual yields in tonnes based on customizable field acreage.
- **Interactive Visual Analytics:** Dynamically renders bar charts comparing yields and smooth splined curves representing yield decay rates across time.
- **Premium User Experience:** Implements an HSL-tailored dark agriculture theme, SVG film-grain texture, smooth micro-animations, and full-glassmorphic panels.

---

## 2. Project Architecture

The application has been refactored into a highly modular, decoupled architecture, separating data definitions, math engines, visualization, and network routing.

```text
AGROSIM/
├── backend/
│   ├── __init__.py
│   ├── main.py        # API router, static files server, and orchestrator
│   ├── models.py      # Pydantic schemas, crop constants, & Markov matrices
│   ├── engine.py      # Simulation calculations, weather generator, and heuristics
│   └── visuals.py     # Matplotlib-based chart rendering & base64 encoding
├── frontend/
│   ├── assets/        # Visual media (e.g., background imagery)
│   ├── index.html     # Single-Page Application (HTML structure and dynamic vanilla JS)
│   └── index.css      # Custom dark-theme styling, glassmorphism, and responsive layout
├── requirements.txt   # Third-party dependency definitions
└── README.md          # Project Master Documentation (This file)
```

### Module Breakdown
*   **`backend/models.py`**: Defines the data models using **Pydantic** for rigid input validation and response serialization. Stores fixed crop traits (`CROP_TRAITS`), climate Markov matrices (`MARKOV_TRANSITIONS`), irrigation thresholds (`IRRIGATION_THRESHOLDS`), and amount rules.
*   **`backend/engine.py`**: The math engine. It computes stationary probabilities for the climate, generates synthetic daily weather, runs the step-by-step weekly soil moisture drawdown simulation, and implements the policy recommendation heuristic.
*   **`backend/visuals.py`**: A graphics painter. It handles styling for the data visualization and produces base64-encoded PNG charts to eliminate standard disk-read/write bottlenecks during network requests.
*   **`backend/main.py`**: The API controller. Sets up the **FastAPI** application, configures static asset serving, exposes endpoints for simulations and sample weather patterns, and coordinates engine computations and visual output.
*   **`frontend/index.html` & `index.css`**: The presentation layer. Houses the modern dark aesthetic using custom variables, responsive Flexbox/Grid layouts, and a film-grain SVG filter. Leverages asynchronous JavaScript (`fetch`) to handle state transitions between the Landing Screen and the live Dashboard.

---

## 3. Mathematical & Simulation Models

The core of AgriSim is driven by empirical agricultural and mathematical equations.

### A. Markov Chain Climate Engine
AgriSim models weather transitions using a discrete-time Markov Chain with three states:
1.  **Normal ($S_0$)**
2.  **Pre-Drought ($S_1$)**
3.  **Drought ($S_2$)**

For each selected drought severity, a transition matrix $P$ controls state probability transitions:

$$P = \begin{pmatrix} P_{00} & P_{01} & P_{02} \\ P_{10} & P_{11} & P_{12} \\ P_{20} & P_{21} & P_{22} \end{pmatrix}$$

For example, in an **Extreme Drought**, the transition matrix is:

$$P_{\text{extreme}} = \begin{pmatrix} 0.55 & 0.30 & 0.15 \\ 0.15 & 0.35 & 0.50 \\ 0.02 & 0.13 & 0.85 \end{pmatrix}$$

This indicates an $85\%$ chance that if a day is in a Drought state, it will remain in a Drought state the next day.

#### Long-Term Stationary Probabilities
The engine solves for the stationary distribution vector $\pi = [\pi_{\text{normal}}, \pi_{\text{pre-drought}}, \pi_{\text{drought}}]$ such that:

$$\pi \cdot P = \pi \quad \text{and} \quad \sum \pi_i = 1$$

This is calculated programmatically in `calculate_pi` by iteratively multiplying a uniform vector over $500$ transition loops. The resulting $\pi_{\text{drought}}$ represents the **Drought Chance** ($D_c$), which acts as a scaling multiplier for the rest of the simulation.

---

### B. Weather Sampling & Distribution
When simulating specific daily profiles, the engine samples rainfall and temperature from distinct mathematical probability distributions:

*   **Rainfall ($R_t$)**: Modeled using a **Gamma Distribution** (skewed, non-negative events):
    
    $$R_t \sim \text{Gamma}(k_s, \theta_s)$$
    
    *   *Normal State ($S_0$)*: High shape and scale: $k = 2.0$, $\theta = 4.0$ (frequent, rich rainfall).
    *   *Drought State ($S_2$)*: Low shape and scale: $k = 0.5$, $\theta = 0.5$ (extremely scarce, low rainfall).

*   **Temperature ($T_t$)**: Modeled using a **Normal (Gaussian) Distribution**:
    
    $$T_t \sim \mathcal{N}(\mu_s, \sigma_s^2)$$
    
    *   *Normal State ($S_0$)*: Modest average heat: $\mu = 1.0$, $\sigma = 1.0$.
    *   *Drought State ($S_2$)*: Increased ambient heat: $\mu = 3.5$, $\sigma = 1.0$.

---

### C. Soil Moisture Drawdown Model
The simulation tracks soil moisture ($M_w$) on a weekly step-rate. 
- **Drought Severity Multiplier ($M_d$)**: Calibrated directly from the stationary probability of the Markov Chain:
  
  $$M_d = 0.82 + 1.15 \cdot D_c$$

- **Natural Moisture Decay**: In the absence of intervention, soil moisture drops by:
  
  $$\Delta M_{\text{decay}} = 3.8 \cdot M_d$$

- **Irrigation Logic**: Under active irrigation strategies, if $M_w < \text{Threshold}_{\text{crop, strategy}}$:
  - Check if the elapsed time since the last irrigation exceeds the frequency cap:
    
    $$\Delta t \ge \text{FreqCap}_{\text{strategy}}$$
    
  - If allowed, apply water ($A_{\text{irr}}$) at a specific delivery coefficient ($0.6$), capping soil moisture at $65.0\%$:
    
    $$M_{w,\text{new}} = \min(65.0, M_w + A_{\text{irr}} \cdot 0.6)$$
    
  - Track irrigation volume consumed:
    
    $$W_{\text{added}} = W_{\text{added}} + A_{\text{irr}} \cdot 12.0$$

---

### D. Crop Physiology & Stress Days
Each crop has a unique physiological tolerance index. The baseline duration $D$ of the drought scenario determines the overall crop exposure.

- **Exposure Factor ($E_c$)**: Scaled based on the ratio of the season length relative to a standard 120-day benchmark ($S_s$):
  
  $$E_c = \min(1.35, 0.75 + 0.25 \cdot S_s)$$

- **Days of Stress ($D_{\text{stress}}$)**: Computed as a function of the drought duration (in days), exposure, and drought multiplier:
  
  $$D_{\text{stress}} = \min(D_{\text{days}}, \max(1, \text{round}(D_{\text{days}} \cdot E_c \cdot 0.4 \cdot M_d)))$$

---

### E. Yield Loss & Harvesting Model
Yield reduction is calculated relative to stress days, irrigation efficiency (which represents evaporation and distribution loss), and crop tolerance.

- **Yield Loss Percentage ($L_y$)**:
  
  $$L_y = \frac{D_{\text{stress}} \cdot 1.05 \cdot (1.1 - \text{Efficiency}_{\text{strategy}}) \cdot M_d}{\max(0.4, \text{Tolerance}_{\text{crop}})}$$
  
  *   *Note: $L_y$ is bounded between a minimum of $2.0\%$ and a maximum crop failure floor of $85.0\%$.*

- **Predicted Harvest Amount**: Calculated based on the average yield percentage across drought horizons ($Y_{\text{avg}} = 100.0 - L_{y,\text{avg}}$) and the biological crop baseline yield ($\text{BaseYield}_{\text{crop}}$ in kg/ha):
  
  $$\text{Harvest} = \left(\frac{Y_{\text{avg}}}{100.0}\right) \cdot \text{BaseYield}_{\text{crop}}$$

- **Farm-Wide Harvest Estimate**: Scales the yield to the user's field size ($F_{\text{ha}}$ in hectares) to output total tonnage:
  
  $$\text{Benchmark Harvest (Tonnes)} = F_{\text{ha}} \cdot \left(\frac{\text{BaseYield}_{\text{crop}}}{1000.0}\right)$$
  
  $$\text{Actual Harvest (Tonnes)} = \text{Benchmark Harvest} \cdot \left(\frac{Y_{\text{avg}}}{100.0}\right)$$
  
  $$\text{Total Loss (Tonnes)} = \text{Benchmark Harvest} - \text{Actual Harvest}$$

---

### F. Irrigation Policy & Optimization Heuristic
AgriSim defines four concrete irrigation strategies:

| Strategy | Irrigation Trigger Threshold | Refill Volume | Pumping Frequency Cap | System Efficiency |
| :--- | :--- | :--- | :--- | :--- |
| **Passive** | $0.0\%$ (No irrigation) | $0.0$ mm | Never | $0\%$ |
| **Conservative** | Low threshold (e.g. Maize: $35\%$) | $25.0$ mm | Every 7 days | $85\%$ (Drip/micro-spray) |
| **Adaptive** | Moderate threshold (e.g. Maize: $50\%$) | $35.0$ mm | Every 5 days | $80\%$ (Rotator sprinklers) |
| **Aggressive** | High threshold (e.g. Maize: $60\%$) | $50.0$ mm | Every 3 days | $65\%$ (Heavy overhead gun) |

#### Strategy Optimization Heuristic
The recommendation engine evaluates all four strategies and ranks them by sorting their composite cost index:

$$\text{Cost} = L_y + \frac{W_{\text{used}}}{10000.0}$$

This heuristic penalizes yield loss ($L_y$) directly, while applying a small weight to the total water consumed ($W_{\text{used}}$). This math prevents recommending high-consumption aggressive strategies for highly resilient crops (like Groundnuts), and forces high-irrigation recommendations for thirsty, delicate crops (like Rice or Maize).

---

## 4. Technology Stack

- **Backend Framework:** **FastAPI** (Python 3.9+) - Selected for native asynchronous execution, automatic swagger generation, and fast serialization.
- **Data Validation:** **Pydantic v2** - Enforces strictly typed payloads and returns robust structured JSON.
- **Mathematical Computation:** **NumPy** - Handles randomized matrix generation and probability distributions.
- **Scientific Splines:** **SciPy** - Performs cubic spline interpolation (`make_interp_spline`) to smooth out discrete point series.
- **Data Visualization:** **Matplotlib** - Implements a headless Agg rendering engine to draw dark-styled charts, writing them as byte arrays directly to memory.
- **Frontend Layer:** **Vanilla HTML5, CSS3, & Modern ES6 JavaScript** - Utilizes CSS Grid, Flexbox, backdrop filters, and async-await fetch routines.

---

## 5. Installation & Setup

### Prerequisites
Make sure you have **Python 3.9** or higher installed on your system.

### 1. Clone or Extract the Project
Ensure the project structure matches the layout detailed in [Project Architecture](#2-project-architecture).

### 2. Install Dependencies
Open your terminal in the root directory and install the necessary libraries:

```bash
pip install -r requirements.txt
```

### 3. Run the Server
Launch the FastAPI server using Uvicorn:

```bash
uvicorn backend.main:app --reload
```

*   The `--reload` flag enables auto-reload, so the server restarts automatically when code modifications are made.

### 4. Open the Dashboard
Open your web browser and navigate to:
```text
http://127.0.0.1:8000/
```

---

## 6. Interactive User Journey

1.  **Landing Portal**: The user is greeted by a cinematic screen featuring a full-width rural irrigation background, an organic SVG film-grain overlay, and a prominent call-to-action button: **Run Simulation**.
2.  **Dashboard Transition**: Clicking "Run Simulation" hides the landing portal and triggers a CSS fade-in animation, revealing the two-column dashboard workspace.
3.  **Input Configuration**: 
    - The user selects a crop (e.g., Maize, Groundnuts) and enters a custom field size in hectares.
    - They adjust the drought severity slider and set the season duration (20-120 days).
    - They configure their baseline strategy to evaluate against the alternatives.
4.  **Instant Modeling**: Clicking **Run Simulation** executes the POST API call. The backend runs all four strategies in parallel.
5.  **Output Visualizations**:
    - **Recommended Action**: Provides an instant plain-language explanation of which strategy is mathematically superior.
    - **Scenario Breakdown**: Displays a side-by-side comparative grid showing predicted yields and losses across short and long horizons.
    - **Farm-Wide Harvest Estimate**: Predicts exact tonnages based on field size.
    - **Visual Charts**: Renders two graphical analysis windows showing mean strategy yield bars and a splined timeline curve.

---

## 7. Presentation Talking Points

If you are presenting AgriSim to your classmates or instructors, use this structured script to showcase the technical depth of the application:

1.  **The Agronomic Problem**:
    > "Climate change has made seasonal rainfall highly unpredictable. Farmers are forced to guess their watering schedules. Underwatering results in immediate crop death, while overwatering wastes precious, expensive reservoir resources. AgriSim bridges this gap by translating complex agronomic mathematics into immediate, actionable advice."
2.  **The Markov Chain Foundation**:
    > "Rather than using generic, flat averages, AgriSim generates drought horizons based on mathematical Markov Chains. We compute stationary probabilities to determine long-term drought risks. In an extreme severity setting, our matrices model high drought state persistence, mimicking severe real-world dry spells."
3.  **Demonstrating Contrast (The Groundnut Trial)**:
    > "Let’s select **Groundnuts** under **Extreme Drought** and click Run. Notice that the Decision Support panel recommends a *Conservative* strategy instead of an *Aggressive* one. Why? Because Groundnuts are highly resilient (0.90 drought tolerance). Aggressive watering would waste massive amounts of water for a minimal $1-2\%$ yield difference. The model's heuristic cost function recognizes this and saves the farmer water."
4.  **Demonstrating Crisis (The Maize Trial)**:
    > "Now let's change the crop to **Maize** under **Extreme Drought**. Notice the dramatic change in the graphs. Maize is highly sensitive (0.52 drought tolerance). The line chart shows a rapid yield decay down towards a total crop failure if we remain passive. The recommendation engine immediately shifts to recommending an **Aggressive** or **Adaptive** strategy, begging the farmer to prioritize crop survival over water conservation."
5.  **The Premium Architecture**:
    > "AgriSim isn't just a prototype; it's a modular, decoupled full-stack application. The frontend uses modern glassmorphism and custom SVG turbulence filters to create an organic texture. The backend serves fully structured data models with Pydantic, renders high-fidelity Matplotlib charts directly in-memory, and sends them via base64 to eliminate slow file-system access."
