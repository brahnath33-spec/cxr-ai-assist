"""Grad-CAM explainability endpoint."""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.v1.schemas.explain import ExplainResponse
from app.config import get_settings
from app.core.gradcam import GradCAMEngine, get_gradcam_engine
from app.core.inference import InferenceEngine, get_inference_engine
from app.core.preprocess import preprocess_bytes
from app.utils.logger import get_logger

router = APIRouter(prefix="/predict", tags=["Prediction"])
logger = get_logger(__name__)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}


@router.post(
    "/explain",
    response_model=ExplainResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze and explain a chest X-ray",
    description=(
        "Upload a chest X-ray and receive predictions plus a Grad-CAM heatmap "
        "showing which regions of the image contributed to the prediction."
    ),
)
async def explain_xray(
    file: UploadFile = File(..., description="Chest X-ray image"),
    target_label: Optional[str] = Form(
        None, description="Pathology to explain (defaults to highest confidence)"
    ),
    inference_engine: InferenceEngine = Depends(get_inference_engine),
    gradcam_engine: GradCAMEngine = Depends(get_gradcam_engine),
) -> ExplainResponse:
    settings = get_settings()

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}",
        )

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )
    if len(contents) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file.")

    try:
        preprocessed, original_image = preprocess_bytes(contents)
        result = inference_engine.predict(preprocessed)
    except Exception as e:
        logger.exception("explain_preprocess_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inference failed.",
        )

    predictions = result["predictions"]

    if target_label and target_label in predictions:
        chosen_label = target_label
    else:
        chosen_label = max(predictions, key=predictions.get)

    heatmap_data = None
    if gradcam_engine.is_loaded:
        heatmap_data = gradcam_engine.generate(preprocessed, original_image, chosen_label)
        if heatmap_data is None:
            logger.warning("heatmap_generation_returned_none", label=chosen_label)

    flagged = [label for label, prob in predictions.items() if prob >= 0.5]

    return ExplainResponse(
        status="success",
        predictions=predictions,
        confidence=result["confidence"],
        flagged=flagged,
        target_label=chosen_label,
        heatmap=heatmap_data,
        model_version=result["model_version"],
        inference_time_ms=result["inference_time_ms"],
        image_dimensions=list(original_image.size),
    )