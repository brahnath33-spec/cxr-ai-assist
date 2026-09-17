"""Reports API — list, view, delete past predictions."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.reports import ReportDetail, ReportSummary
from app.db.database import Report, get_db
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])


def _to_summary(r: Report) -> ReportSummary:
    predictions = r.predictions or {}
    top_finding = max(predictions, key=predictions.get) if predictions else "Unknown"
    return ReportSummary(
        id=r.id,
        filename=r.filename,
        created_at=r.created_at,
        model_version=r.model_version,
        confidence=r.confidence,
        top_finding=top_finding,
        flagged=r.flagged or [],
        image_dimensions=r.image_dimensions or [0, 0],
    )


@router.get("", response_model=List[ReportSummary])
def list_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    reports = (
        db.query(Report)
        .order_by(Report.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_to_summary(r) for r in reports]


@router.get("/{report_id}", response_model=ReportDetail)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    predictions = report.predictions or {}
    top_finding = max(predictions, key=predictions.get) if predictions else "Unknown"
    return ReportDetail(
        id=report.id,
        filename=report.filename,
        created_at=report.created_at,
        model_version=report.model_version,
        confidence=report.confidence,
        top_finding=top_finding,
        flagged=report.flagged or [],
        image_dimensions=report.image_dimensions or [0, 0],
        predictions=predictions,
        inference_time_ms=report.inference_time_ms or 0,
        image_data_url=report.image_data_url,
        heatmap_data_url=report.heatmap_data_url,
    )


@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(report)
    db.commit()
    return {"status": "deleted", "id": report_id}