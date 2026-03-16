"""商品マスタ参照ロジック - POS/売上データ用"""
from dataclasses import dataclass
from typing import Optional, List
from app.db.session import SessionLocal
from app.db.base import ProductMaster


@dataclass
class ProductEmissionResult:
    product_code: str
    product_name: str
    category: str
    scope: int
    emission_factor: float
    emission_unit: str
    quantity: float
    total_emission: float
    data_source: Optional[str] = None
    matched: bool = True


def lookup_product_emission(
    product_code: str,
    quantity: float = 1.0,
) -> Optional[ProductEmissionResult]:
    """商品コードで商品マスタを参照し、排出量を計算する。
    
    Args:
        product_code: 商品コード (SKU)
        quantity: 数量
    
    Returns:
        ProductEmissionResult または None（商品が見つからない場合）
    """
    db = SessionLocal()
    try:
        product = db.query(ProductMaster).filter(
            ProductMaster.product_code == product_code,
            ProductMaster.is_active == 1
        ).first()
        
        if not product:
            return None
        
        total_emission = product.emission_factor * quantity
        
        return ProductEmissionResult(
            product_code=product.product_code,
            product_name=product.product_name,
            category=product.category,
            scope=product.scope,
            emission_factor=product.emission_factor,
            emission_unit=product.emission_unit,
            quantity=quantity,
            total_emission=round(total_emission, 6),
            data_source=product.data_source,
            matched=True,
        )
    finally:
        db.close()


def lookup_products_by_codes(
    product_codes: List[str],
) -> dict:
    """複数商品コードを一括参照。
    
    Args:
        product_codes: 商品コードのリスト
    
    Returns:
        {product_code: ProductEmissionResult or None} の辞書
    """
    db = SessionLocal()
    try:
        products = db.query(ProductMaster).filter(
            ProductMaster.product_code.in_(product_codes),
            ProductMaster.is_active == 1
        ).all()
        
        result = {}
        for code in product_codes:
            product = next((p for p in products if p.product_code == code), None)
            if product:
                result[code] = ProductEmissionResult(
                    product_code=product.product_code,
                    product_name=product.product_name,
                    category=product.category,
                    scope=product.scope,
                    emission_factor=product.emission_factor,
                    emission_unit=product.emission_unit,
                    quantity=1.0,  # quantity is set later
                    total_emission=0.0,  # calculated later
                    data_source=product.data_source,
                    matched=True,
                )
            else:
                result[code] = None
        
        return result
    finally:
        db.close()


def get_category_summary(
    product_results: List[ProductEmissionResult],
) -> dict:
    """カテゴリ別集計。
    
    Args:
        product_results: ProductEmissionResult のリスト
    
    Returns:
        カテゴリ別排出量サマリー
    """
    summary = {}
    for r in product_results:
        cat = r.category
        if cat not in summary:
            summary[cat] = {"total": 0.0, "count": 0, "scope": r.scope}
        summary[cat]["total"] += r.total_emission
        summary[cat]["count"] += 1
    
    return summary


def get_scope_summary(
    product_results: List[ProductEmissionResult],
) -> dict:
    """Scope 別集計。
    
    Args:
        product_results: ProductEmissionResult のリスト
    
    Returns:
        Scope 別排出量サマリー
    """
    summary = {"scope1": 0.0, "scope2": 0.0, "scope3": 0.0}
    for r in product_results:
        key = f"scope{r.scope}"
        summary[key] += r.total_emission
    
    summary["grand_total"] = summary["scope1"] + summary["scope2"] + summary["scope3"]
    return summary
