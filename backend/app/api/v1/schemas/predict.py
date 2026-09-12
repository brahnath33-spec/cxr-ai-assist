"""Request/response schemas for the prediction endpoint."""

from typing import Dict, List

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    """Response returned from /api/v1/predict."""

    status: str = Field(..., description="'success' or 'error'")
    predictions: Dict[str, float] = Field(
        ..., description="Pathology name -> probability (0 to 1)"
    )
    confidence: float = Field(..., description="Max probability across labels")
    flagged: List[str] = Field(
        default_factory=list,
        description="Labels above clinical threshold (0.5)",
    )
    model_version: str
    inference_time_ms: float
    image_dimensions: List[int] = Field(..., description="[width, height]")