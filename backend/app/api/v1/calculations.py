"""算出API: 排出量算出・Scope集計・再計算"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.aggregation import aggregate_by_scope
from app.core.calculator import process_accounting_row
from app.core.factor_repository import LATEST_VERSION
from app.db.base import (
    AuditLog, CalculationJob, CalculationResult, ColumnMapping,
    DataUpload, ScopeSummary as ScopeSummaryDB, UploadRow,
)
from app.db.session import get_db

router = APIRouter()


@router.get("")
def list_jobs(db: Session = Depends(get_db)):
    """過去の算出ジョブ一覧を返す。"""
    jobs = db.query(CalculationJob).order_by(CalculationJob.created_at.desc()).all()
    result = []
    for j in jobs:
        summary = db.query(ScopeSummaryDB).filter(ScopeSummaryDB.job_id == j.id).first()
        result.append({
            "job_id": j.id,
            "upload_id": j.upload_id,
            "emission_factor_version": j.emission_factor_version,
            "status": j.status,
            "created_at": str(j.created_at) if j.created_at else None,
            "grand_total": summary.grand_total if summary else 0,
        })
    return {"jobs": result}


class CalculationRequest(BaseModel):
    upload_id: str
    emission_factor_version: Optional[str] = None


class RecalculateRequest(BaseModel):
    emission_factor_version: Optional[str] = None


class CalculationResponse(BaseModel):
    job_id: str
    upload_id: str
    status: str
    emission_factor_version: str


@router.post("", status_code=202, response_model=CalculationResponse)
def start_calculation(body: CalculationRequest, db: Session = Depends(get_db)):
    """算出ジョブを開始し、同期で処理する（PoC用）。"""
    upload = db.query(DataUpload).filter(DataUpload.id == body.upload_id).first()
    if not upload or upload.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Upload not found")

    version = body.emission_factor_version or LATEST_VERSION

    # ColumnMapping取得（最新）
    mapping_record = (
        db.query(ColumnMapping)
        .filter(ColumnMapping.upload_id == body.upload_id)
        .order_by(ColumnMapping.created_at.desc())
        .first()
    )
    column_mapping = mapping_record.mappings if mapping_record else None

    # ジョブ作成
    job_id = str(uuid.uuid4())
    job = CalculationJob(
        id=job_id,
        upload_id=body.upload_id,
        emission_factor_version=version,
        status="running",
    )
    db.add(job)
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        action="calculation_started",
        resource_type="calculation_job",
        resource_id=job_id,
        detail={"upload_id": body.upload_id, "version": version},
    ))
    db.commit()

    # 算出実行
    rows = (
        db.query(UploadRow)
        .filter(UploadRow.upload_id == body.upload_id)
        .order_by(UploadRow.row_index)
        .all()
    )

    emission_results = []
    for row in rows:
        from app.core.emission import EmissionResult
        if column_mapping:
            result = process_accounting_row(
                row.raw_data, column_mapping, version
            )
        else:
            result = EmissionResult(
                amount_kg_co2e=0.0, scope=None,
                status="unclassified", error_message="No mapping"
            )
        result.row_id = str(row.row_index)
        emission_results.append(result)

        db.add(CalculationResult(
            id=str(uuid.uuid4()),
            job_id=job_id,
            row_index=row.row_index,
            activity_type=result.activity_type,
            scope=result.scope,
            amount_kg_co2e=result.amount_kg_co2e,
            status=result.status,
            error_message=result.error_message,
        ))

    # Scope集計
    summary = aggregate_by_scope(emission_results)
    db.add(ScopeSummaryDB(
        id=str(uuid.uuid4()),
        job_id=job_id,
        scope1_total=summary.scope1_total,
        scope2_total=summary.scope2_total,
        scope3_total=summary.scope3_total,
        grand_total=summary.grand_total,
        total_row_count=summary.total_row_count,
        calculated_row_count=summary.calculated_row_count,
        unclassified_count=summary.unclassified_count,
    ))

    job.status = "completed"
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        action="calculation_completed",
        resource_type="calculation_job",
        resource_id=job_id,
        detail={"grand_total_kg": summary.grand_total},
    ))
    db.commit()

    return CalculationResponse(
        job_id=job_id,
        upload_id=body.upload_id,
        status="completed",
        emission_factor_version=version,
    )


@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(CalculationJob).filter(CalculationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job.id, "status": job.status,
            "emission_factor_version": job.emission_factor_version}


@router.get("/{job_id}/results")
def get_results(job_id: str, db: Session = Depends(get_db)):
    job = db.query(CalculationJob).filter(CalculationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    results = (
        db.query(CalculationResult)
        .filter(CalculationResult.job_id == job_id)
        .order_by(CalculationResult.row_index)
        .all()
    )
    summary = db.query(ScopeSummaryDB).filter(ScopeSummaryDB.job_id == job_id).first()

    return {
        "job_id": job_id,
        "status": job.status,
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
        "summary": {
            "scope1_total": summary.scope1_total if summary else 0.0,
            "scope2_total": summary.scope2_total if summary else 0.0,
            "scope3_total": summary.scope3_total if summary else 0.0,
            "grand_total":  summary.grand_total  if summary else 0.0,
            "total_row_count": summary.total_row_count if summary else 0,
            "calculated_row_count": summary.calculated_row_count if summary else 0,
            "unclassified_count": summary.unclassified_count if summary else 0,
        } if summary else {},
    }


@router.post("/{job_id}/recalculate", status_code=202)
def recalculate(job_id: str, body: RecalculateRequest, db: Session = Depends(get_db)):
    """係数バージョンを変えて再計算する。"""
    original_job = db.query(CalculationJob).filter(CalculationJob.id == job_id).first()
    if not original_job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 元データが削除されていないか確認
    upload = db.query(DataUpload).filter(DataUpload.id == original_job.upload_id).first()
    if not upload or upload.deleted_at is not None:
        raise HTTPException(status_code=409, detail="Source data has been deleted")

    version = body.emission_factor_version or LATEST_VERSION
    from app.api.v1.calculations import start_calculation
    from app.api.v1.calculations import CalculationRequest
    req = CalculationRequest(
        upload_id=original_job.upload_id,
        emission_factor_version=version,
    )
    result = start_calculation(req, db)
    # 親ジョブIDを記録
    new_job = db.query(CalculationJob).filter(CalculationJob.id == result.job_id).first()
    if new_job:
        new_job.parent_job_id = job_id
        db.commit()

    return {
        "job_id": result.job_id,
        "status": result.status,
        "emission_factor_version": version,
    }
