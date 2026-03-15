"""Scope別集計ロジック - 純粋関数"""
from dataclasses import dataclass, field
from typing import List

from app.core.emission import EmissionResult


@dataclass
class ScopeSummary:
    scope1_total: float = 0.0
    scope2_total: float = 0.0
    scope3_total: float = 0.0
    grand_total: float = 0.0
    total_row_count: int = 0
    calculated_row_count: int = 0
    unclassified_count: int = 0
    error_count: int = 0


def aggregate_by_scope(results: List[EmissionResult]) -> ScopeSummary:
    """EmissionResultリストをScope別集計する純粋関数。"""
    s = ScopeSummary(total_row_count=len(results))

    for r in results:
        if r.status == "unclassified" or r.scope is None:
            s.unclassified_count += 1
            continue
        if r.status == "error" or r.amount_kg_co2e is None:
            s.error_count += 1
            continue
        s.calculated_row_count += 1
        if r.scope == 1:
            s.scope1_total += r.amount_kg_co2e
        elif r.scope == 2:
            s.scope2_total += r.amount_kg_co2e
        elif r.scope == 3:
            s.scope3_total += r.amount_kg_co2e

    s.scope1_total = round(s.scope1_total, 6)
    s.scope2_total = round(s.scope2_total, 6)
    s.scope3_total = round(s.scope3_total, 6)
    s.grand_total  = round(s.scope1_total + s.scope2_total + s.scope3_total, 6)
    return s
