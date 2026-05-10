from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple
from pydantic import BaseModel, Field

# Choices for the farmer
StrategyName = Literal["passive", "conservative", "adaptive", "aggressive"]
CropType = Literal["maize", "wheat", "sorghum", "groundnuts", "tobacco"]
DroughtSeverity = Literal["mild", "moderate", "extreme"]

@dataclass(frozen=True)
class CropTraits:
    drought_tolerance: float
    water_requirement: float
    growth_rate: float
    base_yield_kg_ha: float

CROP_TRAITS: Dict[CropType, CropTraits] = {
    "maize": CropTraits(0.52, 1.12, 1.0, 1500.0),
    "wheat": CropTraits(0.72, 0.92, 0.88, 5000.0),
    "sorghum": CropTraits(0.85, 0.65, 0.95, 800.0),
    "groundnuts": CropTraits(0.90, 0.50, 0.90, 1500.0),
    "tobacco": CropTraits(0.80, 0.80, 1.0, 2000.0),
}

MARKOV_TRANSITIONS: Dict[DroughtSeverity, List[List[float]]] = {
    "mild": [
        [0.80, 0.18, 0.02],
        [0.40, 0.42, 0.18],
        [0.10, 0.25, 0.65]
    ],
    "moderate": [
        [0.70, 0.25, 0.05],
        [0.30, 0.40, 0.30],
        [0.05, 0.20, 0.75]
        ],
    "extreme": [
        [0.55, 0.30, 0.15],
        [0.15, 0.35, 0.50],
        [0.02, 0.13, 0.85]
        ],
}

SEVERITY_DURATIONS: Dict[DroughtSeverity, Tuple[int, int]] = {
    "mild": (2, 5), "moderate": (3, 8), "extreme": (5, 12),
}

IRRIGATION_THRESHOLDS: Dict[CropType, Dict[StrategyName, float]] = {
    "maize":      {"passive": 0.0, "conservative": 35.0, "adaptive": 50.0, "aggressive": 60.0},
    "sorghum":    {"passive": 0.0, "conservative": 20.0, "adaptive": 30.0, "aggressive": 40.0},
    "wheat":      {"passive": 0.0, "conservative": 30.0, "adaptive": 45.0, "aggressive": 55.0},
    "groundnuts": {"passive": 0.0, "conservative": 22.0, "adaptive": 32.0, "aggressive": 42.0},
    "tobacco":    {"passive": 0.0, "conservative": 28.0, "adaptive": 42.0, "aggressive": 52.0},
}

IRRIGATION_AMOUNTS: Dict[StrategyName, float] = {
    "passive": 0.0, "conservative": 25.0, "adaptive": 35.0, "aggressive": 50.0
}

IRRIGATION_FREQUENCY_CAP: Dict[StrategyName, int] = {
    "passive": 999, "conservative": 7, "adaptive": 5, "aggressive": 3
}

IRRIGATION_EFFICIENCY: Dict[StrategyName, float] = {
    "passive": 0.0, "conservative": 0.85, "adaptive": 0.80, "aggressive": 0.65
}

ALL_STRATEGIES: List[StrategyName] = ["passive", "conservative", "adaptive", "aggressive"]

class SimulationInput(BaseModel):
    crop_type: CropType = "maize"
    drought_severity: DroughtSeverity = "moderate"
    season_length: int = Field(120, ge=20, le=120)
    irrigation_strategy: StrategyName = "adaptive"
    field_size: float = Field(1.0, ge=0.01, le=10000.0)

class ScenarioResult(BaseModel):
    Weeks: int
    ExpectedYield: float
    ExpectedLoss: float
    DaysOfStress: int
    WaterNeeded: float
    WeeklyMoisture: List[float]

class DailyWeather(BaseModel):
    Day: int
    State: str
    Rain: float
    Temp: float

class ClimateInfo(BaseModel):
    DroughtSeverity: DroughtSeverity
    States: List[str]
    TransitionMatrix: List[List[float]]
    StationaryProbabilities: Dict[str, float]
    DroughtChance: float
    SimulatedWeeks: List[int]

class SimulationLogic(BaseModel):
    StartMoisture: float
    TriggerLevel: float
    StopLevel: float
    EmergencyLevel: float
    WaterBudget: float
    SeasonScale: float

class StrategyEvaluation(BaseModel):
    Strategy: StrategyName
    YieldCurve: Dict[int, float]
    ShortDrought: ScenarioResult
    LongDrought: ScenarioResult
    YieldLoss: float
    AverageYield: float
    HarvestAmount: float
    WaterUsed: float
    IsSafe: bool
    ExpectedYieldTotal: float = 0.0
    ActualYieldTotal: float = 0.0
    TotalLoss: float = 0.0
    LossPercentage: float = 0.0

class Recommendation(BaseModel):
    BestStrategy: StrategyName
    Explanation: str
    YieldWithBest: float
    YieldWithCurrent: float
    WaterWithBest: float
    WaterWithCurrent: float
    Confidence: str

class SimulationResult(BaseModel):
    Inputs: SimulationInput
    Logic: SimulationLogic
    Climate: ClimateInfo
    Evaluations: List[StrategyEvaluation]
    Advice: Recommendation
    PlotMean: str = ""
    PlotCurve: str = ""
