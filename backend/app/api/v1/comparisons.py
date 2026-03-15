"""Comparison endpoint: compare scope summaries across calculation jobs."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.base import CalculationJob, ScopeSummary
from app.db.session import get_db

router = APIRouter()


@router.get("")
def compare_jobs(job_ids: str = Query(..., description="Comma-separated job IDs"), db: Session = Depends(get_db)):
    ids = [jid.strip() for jid in job_ids.split(",") if jid.strip()]
    if len(ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 job_ids required")

    comparisons = []
    for jid in ids:
        job = db.query(CalculationJob).filter(CalculationJob.id == jid).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {jid} not found")
        summary = db.query(ScopeSummary).filter(ScopeSummary.job_id == jid).first()
        if not summary:
            raise HTTPException(status_code=404, detail=f"Summary for job {jid} not found")
        comparisons.append({
            "job_id": jid,
            "factor_version": job.emission_factor_version,
            "scope1_total": summary.scope1_total,
            "scope2_total": summary.scope2_total,
            "scope3_total": summary.scope3_total,
            "grand_total": summary.grand_total,
        })

    first = comparisons[0]
    last = comparisons[-1]
    delta = {
        "scope1": last["scope1_total"] - first["scope1_total"],
        "scope2": last["scope2_total"] - first["scope2_total"],
        "scope3": last["scope3_total"] - first["scope3_total"],
        "grand_total": last["grand_total"] - first["grand_total"],
    }

    return {"comparisons": comparisons, "delta": delta}
