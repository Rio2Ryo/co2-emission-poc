"""排出係数API: 利用可能な排出係数バージョンと値の取得"""
from fastapi import APIRouter

from app.core.factor_repository import AVAILABLE_VERSIONS, DEFAULT_FACTORS

router = APIRouter()


@router.get("")
def list_factors():
    """利用可能な排出係数バージョンとエントリを返す。"""
    versions = {}
    for (activity_type, version), data in DEFAULT_FACTORS.items():
        if version not in versions:
            versions[version] = []
        versions[version].append({
            "activity_type": activity_type,
            "unit": data["unit"],
            "factor_value": data["value"],
            "scope": data["scope"],
        })
    # Sort entries within each version
    for v in versions:
        versions[v].sort(key=lambda x: (x["scope"], x["activity_type"]))
    return {"versions": versions}
