"""Grad-CAM explain endpoint — validated input, smart label selection."""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.v1.schemas.explain import ExplainResponse
from app.config import get_settings
from app.core.gradcam import GradCAMEngine, get_gradcam_engine
from app.core.inference import InferenceEngine, get_inference_engine
from app.core.input_validation import validate_chest_xray
from app.core.preprocess import preprocess_bytes
from app.utils.logger import get_logger

router = APIRouter(prefix="/predict", tags=["Prediction"])
logger = get_logger(__name__)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp",
    "application/dicom", "application/octet-stream",
}
NORMAL_LABEL = "No TB/Pneumonia"
PATHOLOGICAL_LABELS = [
    "Tuberculosis", "Pneumonia",
    "Cardiomegaly", "Pleural Effusion", "Consolidation",
    "Atelectasis", "Pneumothorax",
]


def _pick_explain_label(predictions: dict, requested: Optional[str]) -> str:
    if requested and requested in predictions:
        return requested
    pathological = {k: v for k, v in predictions.items() if k in PATHOLOGICAL_LABELS}
    if pathological:
        top = max(pathological, key=pathological.get)
        if pathological[top] >= 0.05:
            return top
    return NORMAL_LABEL


@router.post("/explain", response_model=ExplainResponse, status_code=status.HTTP_200_OK)
async def explain_xray(
    file: UploadFile = File(..., description="Chest X-ray image"),
    target_label: Optional[str] = Form(None),
    inference_engine: InferenceEngine = Depends(get_inference_engine),
    gradcam_engine: GradCAMEngine = Depends(get_gradcam_engine),
) -> ExplainResponse:
    settings = get_settings()

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large.")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        preprocessed, original_image = preprocess_bytes(contents)
    except Exception as e:
        logger.exception("explain_preprocess_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Could not read image file.")

    # === INPUT VALIDATION ===
    is_valid, reason = validate_chest_xray(original_image, filename=file.filename or "unknown")
    if not is_valid:
        logger.warning("explain_rejected", filename=file.filename, reason=reason)
        raise HTTPException(status_code=400, detail=f"Not a chest X-ray: {reason}")

    try:
        result = inference_engine.predict(preprocessed)
    except Exception as e:
        logger.exception("explain_inference_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Inference failed.")

    predictions = result["predictions"]
    chosen_label = _pick_explain_label(predictions, target_label)

    heatmap_data = None
    if gradcam_engine.is_loaded:
        heatmap_data = gradcam_engine.generate(preprocessed, original_image, chosen_label)

    flagged = [l for l, p in predictions.items() if p >= 0.5 and l != NORMAL_LABEL]

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