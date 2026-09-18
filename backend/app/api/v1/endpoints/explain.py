"""Grad-CAM explain endpoint — auto-selects the most clinically relevant label."""

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
    """Choose which label to explain.

    Rules:
      1. If user requested a specific label → use it.
      2. Else: pick the highest-scoring PATHOLOGICAL label with meaningful signal (>= 0.05).
      3. Else: fall back to the "No TB/Pneumonia" label.
    """
    if requested and requested in predictions:
        return requested

    pathological = {k: v for k, v in predictions.items() if k in PATHOLOGICAL_LABELS}
    if pathological:
        top_label = max(pathological, key=pathological.get)
        if pathological[top_label] >= 0.05:
            return top_label

    return NORMAL_LABEL


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
        None, description="Pathology to explain (defaults to highest pathological confidence)"
    ),
    inference_engine: InferenceEngine = Depends(get_inference_engine),
    gradcam_engine: GradCAMEngine = Depends(get_gradcam_engine),
) -> ExplainResponse:
    settings = get_settings()

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB} MB.")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        preprocessed, original_image = preprocess_bytes(contents)
        result = inference_engine.predict(preprocessed)
    except Exception as e:
        logger.exception("explain_preprocess_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Inference failed.")

    predictions = result["predictions"]
    chosen_label = _pick_explain_label(predictions, target_label)
    logger.info("explain_label_chosen", requested=target_label, chosen=chosen_label, pred_value=predictions.get(chosen_label))

    heatmap_data = None
    if gradcam_engine.is_loaded:
        heatmap_data = gradcam_engine.generate(preprocessed, original_image, chosen_label)
        if heatmap_data is None:
            logger.warning("heatmap_generation_returned_none", label=chosen_label)
    else:
        logger.warning("gradcam_engine_not_loaded")

    flagged = [label for label, prob in predictions.items() if prob >= 0.5 and label != NORMAL_LABEL]

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