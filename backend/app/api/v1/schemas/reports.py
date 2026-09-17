"""Schemas for the Reports API."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class ReportSummary(BaseModel):
    id: int
    filename: str
    created_at: datetime
    model_version: str
    confidence: float
    top_finding: str
    flagged: List[str]
    image_dimensions: List[int]

    class Config:
        from_attributes = True


class ReportDetail(ReportSummary):
    predictions: Dict[str, float]
    inference_time_ms: float
    image_data_url: Optional[str] = None
    heatmap_data_url: Optional[str] = None