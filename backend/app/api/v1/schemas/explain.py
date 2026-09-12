"""Request/response schemas for the Grad-CAM explain endpoint."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ExplainResponse(BaseModel):
    """Response returned from /api/v1/predict/explain."""

    status: str = Field(..., description="'success' or 'error'")
    predictions: Dict[str, float] = Field(
        ..., description="Pathology name -> probability"
    )
    confidence: float
    flagged: List[str]
    target_label: str = Field(..., description="Label used for Grad-CAM")
    heatmap: Optional[str] = Field(
        None, description="Base64 data URL of the heatmap overlay PNG"
    )
    model_version: str
    inference_time_ms: float
    image_dimensions: List[int]