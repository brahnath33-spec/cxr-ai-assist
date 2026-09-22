"""Prediction response schema with optional CTR measurement."""

from typing import Dict, List, Optional
from pydantic import BaseModel


class CTRMeasurement(BaseModel):
    ctr: float
    interpretation: str
    heart_width_px: int
    thorax_width_px: int


class PredictionResponse(BaseModel):
    status: str
    predictions: Dict[str, float]
    confidence: float
    flagged: List[str]
    model_version: str
    inference_time_ms: float
    image_dimensions: List[int]
    ctr: Optional[CTRMeasurement] = None