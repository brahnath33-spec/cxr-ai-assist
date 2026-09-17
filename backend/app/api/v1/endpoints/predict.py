"""Chest X-ray prediction endpoint — saves every analysis to the reports DB."""

import base64
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image

from app.api.v1.schemas.predict import PredictionResponse
from app.config import get_settings
from app.core.inference import InferenceEngine, get_inference_engine
from app.core.preprocess import preprocess_bytes
from app.db.database import Report, SessionLocal
from app.utils.logger import get_logger

router = APIRouter(prefix="/predict", tags=["Prediction"])
logger = get_logger(__name__)

CLINICAL_THRESHOLD = 0.5
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp",
    "application/dicom", "application/octet-stream",
}


def _make_preview(image: Image.Image, max_size: int = 512) -> str:
    """Resize image to a small preview and return as data URL."""
    preview = image.copy()
    preview.thumbnail((max_size, max_size))
    if preview.mode != "RGB":
        preview = preview.convert("RGB")
    buf = io.BytesIO()
    preview.save(buf, format="JPEG", quality=70)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _save_report(filename, result, flagged, dimensions, preview_url, heatmap_url=None):
    """Persist a report to SQLite. Never raises — prediction should not fail on DB error."""
    try:
        db = SessionLocal()
        try:
            report = Report(
                filename=filename,
                model_version=result["model_version"],
                predictions=result["predictions"],
                confidence=result["confidence"],
                flagged=flagged,
                inference_time_ms=result["inference_time_ms"],
                image_dimensions=list(dimensions),
                image_data_url=preview_url,
                heatmap_data_url=heatmap_url,
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            logger.info("report_saved", report_id=report.id, filename=filename)
            return report.id
        finally:
            db.close()
    except Exception as e:
        logger.exception("report_save_failed", error=str(e))
        return None


@router.post("/", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
async def predict_xray(
    file: UploadFile = File(..., description="Chest X-ray image"),
    engine: InferenceEngine = Depends(get_inference_engine),
) -> PredictionResponse:
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
        result = engine.predict(preprocessed)
    except Exception as e:
        logger.exception("prediction_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Inference failed.")

    flagged = [l for l, p in result["predictions"].items() if p >= CLINICAL_THRESHOLD]

    # Build preview and save to DB
    try:
        preview_url = _make_preview(original_image)
        _save_report(
            filename=file.filename or "unknown",
            result=result,
            flagged=flagged,
            dimensions=original_image.size,
            preview_url=preview_url,
        )
    except Exception as e:
        logger.exception("preview_failed", error=str(e))

    logger.info(
        "prediction_completed",
        filename=file.filename,
        flagged=flagged,
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