"""Chest X-ray prediction endpoint."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.v1.schemas.predict import PredictionResponse
from app.config import get_settings
from app.core.inference import InferenceEngine, get_inference_engine
from app.core.preprocess import preprocess_bytes
from app.utils.logger import get_logger

router = APIRouter(prefix="/predict", tags=["Prediction"])
logger = get_logger(__name__)

CLINICAL_THRESHOLD = 0.5
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "application/dicom",
    "application/octet-stream",
}


@router.post(
    "/",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a chest X-ray",
    description="Upload a chest X-ray and receive multi-label pathology predictions.",
)
async def predict_xray(
    file: UploadFile = File(..., description="Chest X-ray image"),
    engine: InferenceEngine = Depends(get_inference_engine),
) -> PredictionResponse:
    settings = get_settings()

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}",
        )

    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file.",
        )

    try:
        preprocessed, original_image = preprocess_bytes(contents)
        result = engine.predict(preprocessed)
    except Exception as e:
        logger.exception("prediction_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inference failed. Please check the uploaded image.",
        )

    flagged = [
        label for label, prob in result["predictions"].items()
        if prob >= CLINICAL_THRESHOLD
    ]

    logger.info(
        "prediction_completed",
        filename=file.filename,
        flagged=flagged,
        model_version=result["model_version"],
        inference_time_ms=result["inference_time_ms"],
    )

    return PredictionResponse(
        status="success",
        predictions=result["predictions"],
        confidence=result["confidence"],
        flagged=flagged,
        model_version=result["model_version"],
        inference_time_ms=result["inference_time_ms"],
        image_dimensions=list(original_image.size),
    )