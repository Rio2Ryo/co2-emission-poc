"""レポート出力API: CSV/JSON形式のレポート生成"""
import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.base import CalculationJob, CalculationResult, DataUpload, ScopeSummary
from app.db.session import get_db

router = APIRouter()


@router.get("/{job_id}/json")
def export_json(job_id: str, db: Session = Depends(get_db)):
    """算出結果をJSON形式でエクスポートする。"""
    job = db.query(CalculationJob).filter(CalculationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Calculation not completed yet")

    upload = db.query(DataUpload).filter(DataUpload.id == job.upload_id).first()
    results = (
        db.query(CalculationResult)
        .filter(CalculationResult.job_id == job_id)
        .order_by(CalculationResult.row_index)
        .all()
    )
    summary = db.query(ScopeSummary).filter(ScopeSummary.job_id == job_id).first()

    return {
        "metadata": {
            "job_id": job.id,
            "emission_factor_version": job.emission_factor_version,
            "created_at": str(job.created_at) if job.created_at else None,
            "data_type": upload.data_type if upload else None,
        },
        "summary": {
            "scope1_total": summary.scope1_total if summary else 0,
            "scope2_total": summary.scope2_total if summary else 0,
            "scope3_total": summary.scope3_total if summary else 0,
            "grand_total": summary.grand_total if summary else 0,
        },
        "rows": [
            {
                "row_index": r.row_index,
                "activity_type": r.activity_type,
                "scope": r.scope,
                "amount_kg_co2e": r.amount_kg_co2e,
                "status": r.status,
            }
            for r in results
        ],
    }


@router.get("/{job_id}/csv")
def export_csv(job_id: str, db: Session = Depends(get_db)):
    """算出結果をCSVエクスポートする。"""
    job = db.query(CalculationJob).filter(CalculationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Calculation not completed yet")

    results = (
        db.query(CalculationResult)
        .filter(CalculationResult.job_id == job_id)
        .order_by(CalculationResult.row_index)
        .all()
    )
    summary = db.query(ScopeSummary).filter(ScopeSummary.job_id == job_id).first()

    output = io.StringIO()
    writer = csv.writer(output)

    # ヘッダー
    writer.writerow([
        "行番号", "活動種別", "Scope", "排出量(kg-CO2e)", "ステータス", "係数バージョン"
    ])
    for r in results:
        writer.writerow([
            r.row_index + 1,
            r.activity_type or "",
            r.scope or "",
            r.amount_kg_co2e or 0.0,
            r.status,
            job.emission_factor_version,
        ])

    # サマリ行
    if summary:
        writer.writerow([])
        writer.writerow(["【集計】", "", "", "", "", ""])
        writer.writerow(["Scope1合計", "", "", summary.scope1_total, "", ""])
        writer.writerow(["Scope2合計", "", "", summary.scope2_total, "", ""])
        writer.writerow(["Scope3合計", "", "", summary.scope3_total, "", ""])
        writer.writerow(["総排出量",   "", "", summary.grand_total,  "", ""])

    output.seek(0)
    bom = "\ufeff"
    return StreamingResponse(
        iter([bom + output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=emission_report_{job_id[:8]}.csv"},
    )
