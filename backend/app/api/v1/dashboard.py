"""ダッシュボードAPI: 集計統計"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.base import CalculationJob, DataUpload, ScopeSummary
from app.db.session import get_db

router = APIRouter()


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    """全完了ジョブの集計統計を返す。"""
    total_jobs = db.query(CalculationJob).count()
    completed_jobs = db.query(CalculationJob).filter(CalculationJob.status == "completed").count()
    total_uploads = db.query(DataUpload).count()

    agg = db.query(
        func.coalesce(func.sum(ScopeSummary.scope1_total), 0),
        func.coalesce(func.sum(ScopeSummary.scope2_total), 0),
        func.coalesce(func.sum(ScopeSummary.scope3_total), 0),
        func.coalesce(func.sum(ScopeSummary.grand_total), 0),
    ).first()

    s1, s2, s3, total_emissions = agg

    return {
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "total_uploads": total_uploads,
        "total_emissions_kg": float(total_emissions),
        "avg_emissions_per_job": float(total_emissions) / completed_jobs if completed_jobs else 0,
        "scope1_total": float(s1),
        "scope2_total": float(s2),
        "scope3_total": float(s3),
    }
