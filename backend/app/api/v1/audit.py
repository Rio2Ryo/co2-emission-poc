"""監査ログAPI: 操作履歴の取得"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.base import AuditLog
from app.db.session import get_db

router = APIRouter()


@router.get("")
def list_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    action: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """監査ログ一覧を返す。"""
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    total = q.count()
    logs = q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "actor_id": log.actor_id,
                "detail": log.detail,
                "created_at": str(log.created_at) if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
    }
