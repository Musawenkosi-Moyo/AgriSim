from pathlib import Path
from typing import List
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from models import (
    SimulationInput, SimulationResult, DailyWeather, DroughtSeverity,
    MARKOV_TRANSITIONS, ALL_STRATEGIES
)
from engine import (
    prepare_logic, build_climate_report, evaluate_strategy,
    make_recommendation, simulate_weather
)
from visuals import create_charts

app = FastAPI(title="AgriSim", version="0.4.0")

@app.get("/")
def home() -> FileResponse:
    return FileResponse(Path(__file__).resolve().parents[1] / "frontend" / "index.html")

@app.post("/api/simulate", response_model=SimulationResult)
def run_sim(data: SimulationInput) -> SimulationResult:
    # 1. Setup
    logic, traits = prepare_logic(data)
    climate = build_climate_report(data.drought_severity)
    drought_mult = 0.82 + climate.DroughtChance * 1.15

    # 2. Simulate all paths
    evals = []
    for s in ALL_STRATEGIES:
        evals.append(evaluate_strategy(data, s, logic, traits, drought_mult))
            
    # 3. Analyze & Visualize
    advice = make_recommendation(data, evals)
    img1, img2 = create_charts(evals)

    return SimulationResult(
        Inputs=data,
        Logic=logic,
        Climate=climate,
        Evaluations=evals,
        Advice=advice,
        PlotMean=img1,
        PlotCurve=img2
    )

@app.get("/api/weather-sample")
def get_weather(severity: DroughtSeverity = "moderate", days: int = 30) -> List[DailyWeather]:
    return simulate_weather(days, MARKOV_TRANSITIONS[severity])

# Serve static files
root = Path(__file__).resolve().parents[1]
app.mount("/assets", StaticFiles(directory=root / "frontend" / "assets"), name="assets")
app.mount("/static", StaticFiles(directory=root / "frontend"), name="static")
