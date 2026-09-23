"""Prediction response schema with CTR, thresholds, and quality check."""

from typing import Dict, List, Optional
from pydantic import BaseModel


class CTRMeasurement(BaseModel):
    ctr: float
    interpretation: str
    heart_width_px: int
    thorax_width_px: int


class QualityCheck(BaseModel):
    suitable: bool
    warnings: List[str] = []


class PredictionResponse(BaseModel):
    status: str
    predictions: Dict[str, float]
    confidence: float
    flagged: List[str]
    thresholds: Dict[str, float]
    model_version: str
    inference_time_ms: float
    image_dimensions: List[int]
    ctr: Optional[CTRMeasurement] = None
    quality: Optional[QualityCheck] = None