"""POS/売上データ用 CO2 算出 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.db.session import SessionLocal
from app.db.base import (
    DataUpload, UploadRow, ColumnMapping, CalculationJob, 
    CalculationResult, ScopeSummary, ProductMaster
)
from app.core.product_lookup import (
    lookup_product_emission, get_category_summary, get_scope_summary
)

router = APIRouter()


class POSRow(BaseModel):
    """POS データ行"""
    product_code: str
    product_name: Optional[str] = None
    quantity: float = 1.0
    unit_price: Optional[float] = None
    amount: Optional[float] = None
    store: Optional[str] = None
    date: Optional[str] = None


class POSCalculationRequest(BaseModel):
    """POS 算出リクエスト"""
    rows: List[POSRow]
    upload_id: Optional[str] = None


class POSCalculationResult(BaseModel):
    """POS 算出結果"""
    job_id: str
    status: str
    row_count: int
    calculated_count: int
    unclassified_count: int
    scope_summary: Dict[str, float]
    category_summary: Dict[str, Dict[str, Any]]
    rows: List[Dict[str, Any]]


@router.post("", status_code=202, summary="POS/売上データ CO2 算出")
def calculate_pos_emissions(request: POSCalculationRequest):
    """POS/売上データから商品マスタ参照で CO2 排出量を算出"""
    db = SessionLocal()
    try:
        job_id = str(uuid.uuid4())
        results = []
        category_totals = {}
        scope_totals = {"scope1": 0.0, "scope2": 0.0, "scope3": 0.0}
        calculated_count = 0
        unclassified_count = 0
        
        for idx, row in enumerate(request.rows):
            # 商品マスタ参照
            product_result = lookup_product_emission(
                product_code=row.product_code,
                quantity=row.quantity
            )
            
            if product_result:
                # 商品マスタに一致
                result = CalculationResult(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    row_index=idx,
                    activity_type=product_result.category,
                    scope=product_result.scope,
                    activity_amount=product_result.quantity,
                    activity_unit=product_result.emission_unit,
                    emission_factor_value=product_result.emission_factor,
                    amount_kg_co2e=product_result.total_emission,
                    status="calculated",
                )
                results.append(result)
                calculated_count += 1
                
                # カテゴリ集計
                cat = product_result.category
                if cat not in category_totals:
                    category_totals[cat] = {"total": 0.0, "count": 0, "scope": product_result.scope}
                category_totals[cat]["total"] += product_result.total_emission
                category_totals[cat]["count"] += 1
                
                # Scope 集計
                scope_totals[f"scope{product_result.scope}"] += product_result.total_emission
            else:
                # 商品マスタに一致せず
                result = CalculationResult(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    row_index=idx,
                    activity_type=None,
                    scope=None,
                    activity_amount=row.quantity,
                    activity_unit="個",
                    emission_factor_value=None,
                    amount_kg_co2e=0.0,
                    status="unclassified",
                    error_message=f"商品コード {row.product_code} がマスタにありません",
                )
                results.append(result)
                unclassified_count += 1
        
        # 集計保存
        grand_total = scope_totals["scope1"] + scope_totals["scope2"] + scope_totals["scope3"]
        scope_summary = ScopeSummary(
            id=str(uuid.uuid4()),
            job_id=job_id,
            scope1_total=scope_totals["scope1"],
            scope2_total=scope_totals["scope2"],
            scope3_total=scope_totals["scope3"],
            grand_total=grand_total,
            total_row_count=len(request.rows),
            calculated_row_count=calculated_count,
            unclassified_count=unclassified_count,
        )
        
        # ジョブ保存
        job = CalculationJob(
            id=job_id,
            upload_id=request.upload_id if request.upload_id else str(uuid.uuid4()),
            emission_factor_version="product_master_v1",
            status="completed",
            completed_at=datetime.now(),
        )
        
        db.add(job)
        db.add(scope_summary)
        for r in results:
            db.add(r)
        db.commit()
        
        # 結果構築
        rows_response = []
        for idx, row in enumerate(request.rows):
            result = next((r for r in results if r.row_index == idx), None)
            if result and result.status == "calculated":
                rows_response.append({
                    "row_index": idx,
                    "product_code": row.product_code,
                    "product_name": row.product_name,
                    "quantity": row.quantity,
                    "emission_factor": result.emission_factor_value,
                    "scope": result.scope,
                    "emission": result.amount_kg_co2e,
                    "status": "calculated",
                })
            else:
                rows_response.append({
                    "row_index": idx,
                    "product_code": row.product_code,
                    "product_name": row.product_name,
                    "quantity": row.quantity,
                    "emission_factor": None,
                    "scope": None,
                    "emission": 0.0,
                    "status": "unclassified",
                    "error": f"商品コード {row.product_code} がマスタにありません",
                })
        
        return POSCalculationResult(
            job_id=job_id,
            status="completed",
            row_count=len(request.rows),
            calculated_count=calculated_count,
            unclassified_count=unclassified_count,
            scope_summary={
                "scope1": scope_totals["scope1"],
                "scope2": scope_totals["scope2"],
                "scope3": scope_totals["scope3"],
                "grand_total": grand_total,
            },
            category_summary=category_totals,
            rows=rows_response,
        )
    finally:
        db.close()


@router.get("/categories/{job_id}", summary="カテゴリ別集計取得")
def get_category_breakdown(job_id: str):
    """ジョブ ID からカテゴリ別内訳を取得"""
    db = SessionLocal()
    try:
        job = db.query(CalculationJob).filter(CalculationJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="ジョブが見つかりません")
        
        results = db.query(CalculationResult).filter(
            CalculationResult.job_id == job_id,
            CalculationResult.status == "calculated"
        ).all()
        
        category_summary = {}
        for r in results:
            cat = r.activity_type or "unknown"
            if cat not in category_summary:
                category_summary[cat] = {"total": 0.0, "count": 0, "scope": r.scope}
            category_summary[cat]["total"] += r.amount_kg_co2e or 0.0
            category_summary[cat]["count"] += 1
        
        return {"job_id": job_id, "categories": category_summary}
    finally:
        db.close()
