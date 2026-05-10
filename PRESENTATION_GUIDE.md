# AgriSim: Agricultural Resilience Dashboard
**Project Documentation & Presentation Guide**

This document provides a comprehensive overview of the **AgriSim** project. You can use this guide as a reference when presenting the architecture, logic, and features of the application to your class.

---

## 1. Project Overview

**AgriSim** is a full-stack web application designed to help farmers predict crop yields and optimize their water usage during drought conditions. By combining mathematical models (Markov Chains) with crop-specific physiology, the simulation predicts how different irrigation strategies will perform across unpredictable drought horizons.

**Key Value Proposition:**
- Prevent total crop failure during severe droughts.
- Avoid wasting water on highly resilient crops (like Groundnuts or Sorghum) by identifying optimal watering intervals.
- Translate complex agronomic data into plain-language, actionable advice.

---

## 2. Technology Stack

- **Backend:** Python + FastAPI
  - Chosen for its high performance, native asynchronous support, and automatic data validation using Pydantic.
- **Frontend:** Vanilla HTML, CSS (Inter font, dark agriculture aesthetic), and JavaScript.
- **Data Visualization:** Chart.js (for rendering interactive, smoothed curves and bar charts comparing yields).
- **Math & Simulation:** NumPy (for generating random weather distributions based on gamma/normal distributions).

---

## 3. Modular Software Architecture

To ensure the project is maintainable and scalable, I refactored the backend from a single file into a modular architecture. This separation of concerns makes the code much easier to read and present.

### A. `models.py` (The Blueprints)
This file contains all the data structures and fixed agricultural constants:
- **Pydantic Models:** Defines how data is structured for the API (e.g., `SimulationInput`, `SimulationResult`).
- **Crop Traits:** The physiological data for Maize, Wheat, Sorghum, etc.
- **Climate Data:** The Markov transition matrices for different drought severities.

### B. `engine.py` (The Brain)
This is where the core mathematical simulation lives:
- **Markov Chain Engine:** Calculates long-term drought shares and horizons.
- **Yield Simulator:** The physics engine that calculates soil moisture drawdown and crop stress over time.
- **Recommendation Logic:** The heuristic engine that ranks irrigation strategies to find the perfect balance for the farmer.

### C. `visuals.py` (The Painter)
This module is dedicated entirely to data visualization using **Matplotlib**:
- It takes the simulation data and draws high-quality PNG graphs.
- It handles all the styling (fonts, colors, and line smoothing) before sending the images to the web dashboard.

### D. `main.py` (The Entry Point)
This is the glue that connects everything:
- It initializes the **FastAPI** application.
- It handles the network requests (API endpoints) and routes data between the Engine and the Visuals modules.
- It serves the static frontend files to the browser.
- It outputs the absolute best combination of Strategy + Gap in simple, plain English.

---

## 4. The Frontend Interface (`frontend/index.html` & `index.css`)

The frontend is a strictly single-page application built to look like a premium, modern dashboard.

### A. Design Aesthetic
- **Theme:** A cohesive dark-green agriculture theme (`#0d1f0e`) to reduce eye strain and look professional.
- **Textures:** We utilized an advanced SVG `<feTurbulence>` filter to create a subtle film-grain overlay, giving the app a tactile, organic feel.
- **Glassmorphism:** The cards have semi-transparent backgrounds with background-blur effects (`backdrop-filter`), making them look incredibly modern.

### B. User Flow
1. **Landing View:** A hero screen with a clear value proposition ("Predict your harvest before drought decides for you"). 
2. **Simulation Dashboard:** Uses JavaScript to hide the landing page and fade in the dashboard.
   - **Left Panel (Inputs):** The user defines their crop, severity, season length, and tests their own irrigation hypothesis using sliders.
   - **Right Panel (Outputs):** Displays the plain-language recommendation, a scenario breakdown table (showing exactly how yields drop in short vs long droughts), and visual charts.

### C. Data Visualization (Chart.js)
When the user clicks "Run Simulation," the JS sends a payload to the FastAPI backend, receives the JSON response, and dynamically renders two charts:
- A **Bar Chart** showing the mean yield for all four strategies.
- A **Curved Line Chart** (`tension: 0.4`) that plots the trajectory of the crop's yield from "Now" down to the short and long drought horizons, cleanly visualizing the crop's decline.

---

## 5. Talking Points for Your Presentation

When showing this in class, you can structure your demo like this:

1. **The Problem:** Explain that climate change makes rainfall unpredictable. Farmers guess how much to water, leading to either dead crops or wasted reservoirs.
2. **The Solution (AgriSim):** Show the landing page. Explain that this tool mathematically predicts outcomes based on crop biology and Markov climate statistics.
3. **The Demo - Groundnuts:** 
   - Select Groundnuts (a highly resilient crop) and Extreme Drought. 
   - Show how the Recommendation Engine tells the farmer *not* to waste water with aggressive irrigation because Groundnuts are highly drought-tolerant.
4. **The Demo - Rice/Maize:** 
   - Change the crop to Rice or Maize. 
   - Point to the curved line graph to show how rapidly the yield drops toward 0% if they use a Passive strategy. 
   - Show how the Recommendation Engine dynamically adapts, now begging the farmer to use an Aggressive, tight-gap watering strategy to save the crop.
5. **Conclusion:** Summarize that AgriSim bridges the gap between complex agronomic data and actionable, easy-to-understand advice for farmers.
