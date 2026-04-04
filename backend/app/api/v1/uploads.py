"""アップロードAPI: CSV取込 + 列マッピング"""
import csv
import io
import uuid
from typing import Dict, List

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

# 弥生会計CSVの列名定義（ヘッダーなし・25列固定）
YAYOI_COLUMNS = [
    "伝票番号", "行番号", "枝番", "日付",
    "借方勘定科目", "借方補助科目", "借方部門", "借方税区分",
    "借方金額", "借方消費税額",
    "貸方勘定科目", "貸方補助科目", "貸方部門", "貸方税区分",
    "貸方金額", "貸方消費税額",
    "摘要", "予備1", "予備2", "按分",
    "入力形式", "予備3", "会計期間", "予備4", "決算フラグ",
]

# 必須列チェック（会計CSV用・ヘッダーあり形式のみ）
REQUIRED_HEADERS = {"勘定科目名", "金額"}


def _parse_yayoi_csv(text: str):
    """弥生会計エクスポートCSV（ヘッダーなし・25列）をパースして辞書リストに変換する。"""
    reader = csv.reader(io.StringIO(text))
    rows = []
    for row in reader:
        if not row:
            continue
        padded = row + [""] * (len(YAYOI_COLUMNS) - len(row))
        rows.append(dict(zip(YAYOI_COLUMNS, padded[:len(YAYOI_COLUMNS)])))
    return rows


def _is_yayoi_format(first_row_values) -> bool:
    """最初の行の最初の値が4桁の数字なら弥生会計形式と判定する。"""
    if not first_row_values:
        return False
    try:
        v = list(first_row_values)[0]
        return len(str(int(v))) == 4
    except (ValueError, TypeError):
        return False


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
            raise HTTPException(status_code=422, detail="Unsupported encoding (use UTF-8 or Shift-JIS)")

    # 弥生会計形式か通常のDictReader形式かを判定してパース
    try:
        first_reader = csv.reader(io.StringIO(text))
        first_row = next(first_reader, [])
        is_yayoi = _is_yayoi_format(first_row)
        if is_yayoi:
            # 弥生形式: ヘッダーなし・25列固定
            rows = _parse_yayoi_csv(text)
        else:
            # 通常形式: ヘッダーあり
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"CSV parse error: {e}")

    if not rows:
        raise HTTPException(status_code=422, detail="CSV has no data rows")

    headers = list(rows[0].keys()) if rows else []

    # 通常形式の会計CSVのみ必須列チェック（弥生形式はスキップ）
    if data_type == "accounting" and not is_yayoi:
        missing = REQUIRED_HEADERS - set(headers)
        if missing:
            raise HTTPException(
                status_code=422,
                detail=[{"msg": f"Missing required column: {col}"} for col in missing],
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

        try:
            first_reader = csv.reader(io.StringIO(text))
            first_row = next(first_reader, [])
            if _is_yayoi_format(first_row):
                rows = _parse_yayoi_csv(text)
            else:
                rows = list(csv.DictReader(io.StringIO(text)))
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
