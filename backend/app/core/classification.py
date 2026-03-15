"""活動種別・Scope分類ロジック - 純粋関数"""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# 勘定科目コード → (activity_type, scope)
ACCOUNT_CODE_RULES: Dict[str, Tuple[str, int]] = {
    "710": ("electricity",     2),
    "711": ("natural_gas",     1),
    "712": ("lpg",             1),
    "730": ("gasoline",        1),
    "731": ("diesel",          1),
    "740": ("kerosene",        1),
    "750": ("business_travel", 3),
    "760": ("freight",         3),
}

# キーワード → (activity_type, scope) ※コードベースが優先
KEYWORD_RULES: Dict[str, Tuple[str, int]] = {
    "電力":     ("electricity",     2),
    "電気":     ("electricity",     2),
    "都市ガス": ("natural_gas",     1),
    "ガス":     ("natural_gas",     1),
    "ガソリン": ("gasoline",        1),
    "軽油":     ("diesel",          1),
    "灯油":     ("kerosene",        1),
    "旅費":     ("business_travel", 3),
    "出張":     ("business_travel", 3),
    "輸送":     ("freight",         3),
    "物流":     ("freight",         3),
}


@dataclass
class ClassificationResult:
    activity_type: Optional[str]
    scope: Optional[int]
    status: str = "classified"    # "classified" | "unclassified"
    match_method: str = "code"    # "code" | "keyword" | "none"
    rule_priority: Optional[int] = None


def classify_scope(
    account_code: Optional[str] = None,
    account_name: Optional[str] = None,
) -> ClassificationResult:
    """勘定科目コード/名称からScope・活動種別を分類する純粋関数。

    優先順位: 1. コードマッチ  2. キーワードマッチ  3. unclassified
    """
    if account_code and account_code in ACCOUNT_CODE_RULES:
        activity_type, scope = ACCOUNT_CODE_RULES[account_code]
        return ClassificationResult(
            activity_type=activity_type, scope=scope,
            status="classified", match_method="code", rule_priority=1,
        )

    if account_name:
        for keyword, (activity_type, scope) in KEYWORD_RULES.items():
            if keyword in account_name:
                return ClassificationResult(
                    activity_type=activity_type, scope=scope,
                    status="classified", match_method="keyword", rule_priority=2,
                )

    return ClassificationResult(
        activity_type=None, scope=None,
        status="unclassified", match_method="none",
    )
