"""アップロードAPI: CSV取込 + 列マッピング"""
import csv
import io
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from fastapi.responses import Response

from app.db.session import get_db
from app.db.base import (
    AuditLog, CalculationJob, CalculationResult, ColumnMapping,
    DataUpload, ScopeSummary, UploadRow,
)

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"text/csv", "text/plain", "application/csv"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 必須列チェック（会計CSV用）
REQUIRED_HEADERS = {"勘定科目名", "金額"}


class MappingRequest(BaseModel):
    mappings: Dict[str, str]  # {"元列名": "標準列名"}


class UploadResponse(BaseModel):
    upload_id: str
    filename: str
    data_type: str
    row_count: int
    status: str
    headers: List[str]
    preview: List[Dict]


class MappingResponse(BaseModel):
    mapping_id: str
    upload_id: str
    mappings: Dict[str, str]


def _error_detail(message: str, row: Optional[int] = None, column: Optional[str] = None) -> Dict[str, Any]:
    """Unified error detail structure."""
    detail: Dict[str, Any] = {"message": message}
    if row is not None:
        detail["row"] = row
    if column is not None:
        detail["column"] = column
    return detail


def _validate_csv_rows(rows: List[Dict], headers: List[str]) -> List[Dict[str, Any]]:
    """Validate CSV rows and return list of error details (row number + column name)."""
    errors: List[Dict[str, Any]] = []
    for i, row in enumerate(rows, start=2):  # row 1 = header, data starts at row 2
        for col in headers:
            if col not in row:
                errors.append(_error_detail(
                    f"Missing value for column '{col}'",
                    row=i,
                    column=col,
                ))
    return errors


@router.get("")
def list_uploads(db: Session = Depends(get_db)):
    """過去のアップロード一覧を返す。"""
    uploads = db.query(DataUpload).order_by(DataUpload.created_at.desc()).all()
    return {
        "uploads": [
            {
                "upload_id": u.id,
                "filename": u.filename,
                "data_type": u.data_type,
                "row_count": u.row_count,
                "status": u.status,
                "created_at": str(u.created_at) if u.created_at else None,
            }
            for u in uploads
        ]
    }


@router.post("", status_code=201, response_model=UploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    data_type: str = Form("accounting"),
    db: Session = Depends(get_db),
):
    """CSVファイルをアップロードしてプレビューを返す。"""
    # ファイル検証
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=422, detail="File is empty")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
    if not (file.filename or "").endswith(".csv"):
        raise HTTPException(status_code=422, detail="Only .csv files are supported")

    # CSV解析
    try:
        text = content.decode("utf-8-sig")  # BOM付きUTF-8も対応
    except UnicodeDecodeError:
        try:
            text = content.decode("shift_jis")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=422,
                detail=_error_detail("Unsupported file encoding. Please use UTF-8 or Shift-JIS."),
            )

    reader = csv.DictReader(io.StringIO(text))
    try:
        rows = list(reader)
    except csv.Error as e:
        raise HTTPException(
            status_code=422,
            detail=_error_detail(f"Invalid CSV format: {e}"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=_error_detail(f"CSV parse error: {e}"),
        )

    if not rows:
        raise HTTPException(
            status_code=422,
            detail=_error_detail("CSV file contains no data rows (only a header or is empty)."),
        )

    headers = list(rows[0].keys()) if rows else []

    if not headers or all(h.strip() == "" for h in headers):
        raise HTTPException(
            status_code=422,
            detail=_error_detail("CSV has no valid header columns."),
        )

    # 会計CSVの必須列チェック
    if data_type == "accounting":
        missing = REQUIRED_HEADERS - set(headers)
        if missing:
            raise HTTPException(
                status_code=422,
                detail=[
                    _error_detail(f"Missing required column: '{col}'", column=col)
                    for col in sorted(missing)
                ],
            )

    # DB保存
    upload_id = str(uuid.uuid4())
    upload = DataUpload(
        id=upload_id,
        filename=file.filename or "unknown.csv",
        data_type=data_type,
        row_count=len(rows),
        status="pending_mapping",
    )
    db.add(upload)

    for i, row in enumerate(rows):
        db.add(UploadRow(
            id=str(uuid.uuid4()),
            upload_id=upload_id,
            row_index=i,
            raw_data=dict(row),
        ))

    db.add(AuditLog(
        id=str(uuid.uuid4()),
        action="upload_created",
        resource_type="data_upload",
        resource_id=upload_id,
        detail={"filename": file.filename, "row_count": len(rows)},
    ))
    db.commit()

    return UploadResponse(
        upload_id=upload_id,
        filename=file.filename or "",
        data_type=data_type,
        row_count=len(rows),
        status="pending_mapping",
        headers=headers,
        preview=rows[:5],
    )


@router.post("/batch", status_code=201)
async def upload_batch(
    files: List[UploadFile] = File(...),
    data_type: str = Form("accounting"),
    db: Session = Depends(get_db),
):
    """複数CSVファイルを一括アップロードする。"""
    results = []
    for file in files:
        content = await file.read()
        if len(content) == 0 or not (file.filename or "").endswith(".csv"):
            continue

        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = content.decode("shift_jis")
            except UnicodeDecodeError:
                continue

        reader = csv.DictReader(io.StringIO(text))
        try:
            rows = list(reader)
        except Exception:
            continue

        if not rows:
            continue

        upload_id = str(uuid.uuid4())
        upload = DataUpload(
            id=upload_id,
            filename=file.filename or "unknown.csv",
            data_type=data_type,
            row_count=len(rows),
            status="pending_mapping",
        )
        db.add(upload)

        for i, row in enumerate(rows):
            db.add(UploadRow(
                id=str(uuid.uuid4()),
                upload_id=upload_id,
                row_index=i,
                raw_data=dict(row),
            ))

        db.add(AuditLog(
            id=str(uuid.uuid4()),
            action="upload_created",
            resource_type="data_upload",
            resource_id=upload_id,
            detail={"filename": file.filename, "row_count": len(rows), "batch": True},
        ))

        results.append({
            "upload_id": upload_id,
            "filename": file.filename or "",
            "row_count": len(rows),
            "status": "pending_mapping",
        })

    db.commit()
    return {"uploads": results}


@router.post("/{upload_id}/mappings", status_code=201, response_model=MappingResponse)
def save_mapping(
    upload_id: str,
    body: MappingRequest,
    db: Session = Depends(get_db),
):
    """列マッピングを保存する。"""
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    mapping_id = str(uuid.uuid4())
    mapping = ColumnMapping(
        id=mapping_id,
        upload_id=upload_id,
        mappings=body.mappings,
    )
    db.add(mapping)
    upload.status = "ready"
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        action="mapping_saved",
        resource_type="data_upload",
        resource_id=upload_id,
        detail={"mapping_id": mapping_id},
    ))
    db.commit()

    return MappingResponse(
        mapping_id=mapping_id,
        upload_id=upload_id,
        mappings=body.mappings,
    )


@router.get("/{upload_id}")
def get_upload(upload_id: str, db: Session = Depends(get_db)):
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return {"upload_id": upload.id, "status": upload.status, "row_count": upload.row_count}


@router.delete("/{upload_id}", status_code=204)
def delete_upload(upload_id: str, db: Session = Depends(get_db)):
    """アップロードと関連データを全て削除する。"""
    upload = db.query(DataUpload).filter(DataUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    # Delete cascaded data
    jobs = db.query(CalculationJob).filter(CalculationJob.upload_id == upload_id).all()
    for job in jobs:
        db.query(CalculationResult).filter(CalculationResult.job_id == job.id).delete()
        db.query(ScopeSummary).filter(ScopeSummary.job_id == job.id).delete()
    db.query(CalculationJob).filter(CalculationJob.upload_id == upload_id).delete()
    db.query(ColumnMapping).filter(ColumnMapping.upload_id == upload_id).delete()
    db.query(UploadRow).filter(UploadRow.upload_id == upload_id).delete()
    db.delete(upload)

    db.add(AuditLog(
        id=str(uuid.uuid4()),
        action="upload_deleted",
        resource_type="data_upload",
        resource_id=upload_id,
    ))
    db.commit()
    return Response(status_code=204)
