import numpy as np
from typing import List, Tuple, Dict
from models import (
    StrategyName, CropType, DroughtSeverity, CropTraits, CROP_TRAITS,
    MARKOV_TRANSITIONS, SEVERITY_DURATIONS, ALL_STRATEGIES,
    IRRIGATION_THRESHOLDS, IRRIGATION_AMOUNTS, IRRIGATION_FREQUENCY_CAP, IRRIGATION_EFFICIENCY,
    SimulationInput, ScenarioResult, DailyWeather, ClimateInfo,
    SimulationLogic, StrategyEvaluation, Recommendation
)

def calculate_pi(matrix: List[List[float]], loops: int = 500) -> List[float]:
    """Calculate the long-term chance of each weather state."""
    pi = [1/3, 1/3, 1/3]
    for _ in range(loops):
        next_pi = [
            pi[0]*matrix[0][0] + pi[1]*matrix[1][0] + pi[2]*matrix[2][0],
            pi[0]*matrix[0][1] + pi[1]*matrix[1][1] + pi[2]*matrix[2][1],
            pi[0]*matrix[0][2] + pi[1]*matrix[1][2] + pi[2]*matrix[2][2],
        ]
        total = sum(next_pi)
        pi = [x/total for x in next_pi]
    return pi

def prepare_logic(data: SimulationInput) -> Tuple[SimulationLogic, CropTraits]:
    traits = CROP_TRAITS[data.crop_type]
    scale = data.season_length / 120.0
    
    return SimulationLogic(
        StartMoisture=30.0,
        TriggerLevel=30.0,
        StopLevel=42.0,
        EmergencyLevel=18.0,
        WaterBudget=round(6500.0 * traits.water_requirement * scale**0.35, 2),
        SeasonScale=round(scale, 4)
    ), traits

def run_drought_scenario(weeks: int, strategy: StrategyName, crop: CropType, logic: SimulationLogic, traits: CropTraits, drought_mult: float) -> ScenarioResult:
    days = weeks * 7
    
    # Stress calculation
    exposure = min(1.35, 0.75 + 0.25 * logic.SeasonScale)
    stress_days = int(round(days * exposure * 0.4 * drought_mult))
    stress_days = max(1, min(stress_days, days))
    
    # Params
    threshold = IRRIGATION_THRESHOLDS[crop][strategy]
    amount = IRRIGATION_AMOUNTS[strategy]
    efficiency = IRRIGATION_EFFICIENCY[strategy]
    freq_cap = IRRIGATION_FREQUENCY_CAP[strategy]
    
    # Moisture track & Water usage simulation
    moisture_track = []
    current_m = logic.StartMoisture
    total_water = 0.0
    last_irrigation = -999
    
    # Baseline water (maintenance)
    baseline = weeks * 40.0 * traits.water_requirement
    
    for w in range(weeks):
        # Natural moisture decay (impacted by drought)
        current_m = max(4.0, current_m - (3.8 * drought_mult))
        
        # Check if irrigation is needed and allowed
        if strategy != "passive" and current_m < threshold:
            if (w * 7) - last_irrigation >= freq_cap:
                current_m = min(65.0, current_m + amount * 0.6)
                total_water += amount * 12.0 # Scale for total water
                last_irrigation = w * 7
        
        moisture_track.append(round(current_m, 2))

    # Yield Loss
    loss = (stress_days * 1.05 * (1.1 - efficiency) * drought_mult) / max(0.4, traits.drought_tolerance)
    loss = max(2.0, min(loss, 85.0))

    return ScenarioResult(
        Weeks=weeks,
        ExpectedYield=round(100.0 - loss, 2),
        ExpectedLoss=round(loss, 2),
        DaysOfStress=stress_days,
        WaterNeeded=round(baseline + total_water, 2),
        WeeklyMoisture=moisture_track
    )

def evaluate_strategy(data: SimulationInput, strategy: StrategyName, logic: SimulationLogic, traits: CropTraits, drought_mult: float) -> StrategyEvaluation:
    short_w, long_w = SEVERITY_DURATIONS[data.drought_severity]
    
    short = run_drought_scenario(short_w, strategy, data.crop_type, logic, traits, drought_mult)
    long = run_drought_scenario(long_w, strategy, data.crop_type, logic, traits, drought_mult)
    
    avg_yield = round((short.ExpectedYield + long.ExpectedYield) / 2.0, 2)
    harvest = round((avg_yield / 100.0) * traits.base_yield_kg_ha, 2)
    
    # Generate points for the YieldCurve
    curve = {w: run_drought_scenario(w, strategy, data.crop_type, logic, traits, drought_mult).ExpectedYield for w in [0, 2, 4, 8]}

    # Field size calculations (in tonnes)
    expected_total = data.field_size * (traits.base_yield_kg_ha / 1000.0)
    actual_total = expected_total * (avg_yield / 100.0)
    total_loss = expected_total - actual_total
    loss_percent = 100.0 - avg_yield

    return StrategyEvaluation(
        Strategy=strategy,
        YieldCurve=curve,
        ShortDrought=short,
        LongDrought=long,
        YieldLoss=round(100.0 - avg_yield, 2),
        AverageYield=avg_yield,
        HarvestAmount=harvest,
        WaterUsed=round((short.WaterNeeded + long.WaterNeeded) / 2.0, 2),
        IsSafe=avg_yield >= 60.0,
        ExpectedYieldTotal=round(expected_total, 2),
        ActualYieldTotal=round(actual_total, 2),
        TotalLoss=round(total_loss, 2),
        LossPercentage=round(loss_percent, 2)
    )

def make_recommendation(data: SimulationInput, evals: List[StrategyEvaluation]) -> Recommendation:
    current = next((e for e in evals if e.Strategy == data.irrigation_strategy), evals[0])
    best = sorted(evals, key=lambda e: e.YieldLoss + e.WaterUsed/10000.0)[0]
    
    return Recommendation(
        BestStrategy=best.Strategy,
        Explanation=f"Use {best.Strategy} strategy for the best result.",
        YieldWithBest=best.AverageYield,
        YieldWithCurrent=current.AverageYield,
        WaterWithBest=best.WaterUsed,
        WaterWithCurrent=current.WaterUsed,
        Confidence="High"
    )

def build_climate_report(severity: DroughtSeverity) -> ClimateInfo:
    matrix = MARKOV_TRANSITIONS[severity]
    pi = calculate_pi(matrix)
    short_w, long_w = SEVERITY_DURATIONS[severity]
    
    return ClimateInfo(
        DroughtSeverity=severity,
        States=["Normal", "Pre-Drought", "Drought"],
        TransitionMatrix=matrix,
        StationaryProbabilities={"Normal": pi[0], "Pre-Drought": pi[1], "Drought": pi[2]},
        DroughtChance=round(pi[2], 4),
        SimulatedWeeks=[short_w, long_w]
    )

def simulate_weather(days: int, matrix: List[List[float]]) -> List[DailyWeather]:
    series = []
    state = 0
    for d in range(1, days + 1):
        rain = np.random.gamma(2.0, 4.0) if state == 0 else np.random.gamma(0.5, 0.5)
        temp = np.random.normal(1.0, 1.0) if state == 0 else np.random.normal(3.5, 1.0)
        series.append(DailyWeather(Day=d, State=["Normal", "Pre-Drought", "Drought"][state], Rain=round(rain, 2), Temp=round(temp, 2)))
        state = int(np.random.choice([0, 1, 2], p=matrix[state]))
    return series
