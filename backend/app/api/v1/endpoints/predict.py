"""Chest X-ray prediction endpoint - quality gate + CTR + per-label thresholds."""

import base64
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image

from app.api.v1.schemas.predict import CTRMeasurement, PredictionResponse, QualityCheck
from app.config import get_settings
from app.core.ctr import measure_ctr
from app.core.inference import InferenceEngine, get_inference_engine
from app.core.preprocess import preprocess_bytes
from app.core.quality import check_image_quality
from app.core.thresholds import CLINICAL_THRESHOLDS, get_threshold
from app.db.database import Report, SessionLocal
from app.utils.logger import get_logger

router = APIRouter(prefix="/predict", tags=["Prediction"])
logger = get_logger(__name__)

NORMAL_LABEL = "No TB/Pneumonia"
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp",
    "application/dicom", "application/octet-stream",
}


def _make_preview(image: Image.Image, max_size: int = 512) -> str:
    preview = image.copy()
    preview.thumbnail((max_size, max_size))
    if preview.mode != "RGB":
        preview = preview.convert("RGB")
    buf = io.BytesIO()
    preview.save(buf, format="JPEG", quality=70)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _save_report(filename, result, flagged, dimensions, preview_url, ctr_data=None):
    try:
        db = SessionLocal()
        try:
            predictions = dict(result["predictions"])
            if ctr_data is not None:
                predictions["CTR"] = ctr_data["ctr"]
            report = Report(
                filename=filename,
                model_version=result["model_version"],
                predictions=predictions,
                confidence=result["confidence"],
                flagged=flagged,
                inference_time_ms=result["inference_time_ms"],
                image_dimensions=list(dimensions),
                image_data_url=preview_url,
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            logger.info("report_saved", report_id=report.id)
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

    # Preprocess FIRST so we have the image
    try:
        preprocessed, original_image = preprocess_bytes(contents)
    except Exception as e:
        logger.exception("preprocess_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Could not read image file.")

    # Quality gate
    quality_result = check_image_quality(original_image)
    quality = QualityCheck(
        suitable=quality_result["suitable"],
        warnings=quality_result["warnings"],
    )

    # If not suitable, return early with no predictions
    if not quality_result["suitable"]:
        logger.warning("analysis_rejected_by_quality_gate", warnings=quality_result["warnings"])
        return PredictionResponse(
            status="rejected",
            predictions={},
            confidence=0.0,
            flagged=[],
            thresholds=CLINICAL_THRESHOLDS,
            model_version="quality-gate",
            inference_time_ms=0.0,
            image_dimensions=list(original_image.size),
            ctr=None,
            quality=quality,
        )

    # Run inference
    try:
        result = engine.predict(preprocessed)
    except Exception as e:
        logger.exception("prediction_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Inference failed.")

    # CTR measurement
    ctr_result = None
    ctr_data = None
    try:
        ctr_data = measure_ctr(original_image)
        if ctr_data is not None:
            ctr_result = CTRMeasurement(
                ctr=ctr_data["ctr"],
                interpretation=ctr_data["interpretation"],
                heart_width_px=ctr_data["heart_width_px"],
                thorax_width_px=ctr_data["thorax_width_px"],
            )
    except Exception as e:
        logger.exception("ctr_failed", error=str(e))

    # Per-label threshold flagging
    flagged = []
    for label, prob in result["predictions"].items():
        if prob >= get_threshold(label):
            flagged.append(label)

    # Save report
    try:
        preview_url = _make_preview(original_image)
        _save_report(
            filename=file.filename or "unknown",
            result=result,
            flagged=flagged,
            dimensions=original_image.size,
            preview_url=preview_url,
            ctr_data=ctr_data,
        )
    except Exception:
        pass

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
        thresholds=CLINICAL_THRESHOLDS,
        model_version=result["model_version"],
        inference_time_ms=result["inference_time_ms"],
        image_dimensions=list(original_image.size),
        ctr=ctr_result,
        quality=quality,
    )