"""商品マスタ API - CRUD 操作"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.db.session import SessionLocal
from app.db.base import ProductMaster

router = APIRouter()


class ProductCreate(BaseModel):
    product_code: str
    product_name: str
    category: str
    subcategory: Optional[str] = None
    scope: int
    emission_factor: float
    emission_unit: str
    data_source: Optional[str] = None
    description: Optional[str] = None


class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    scope: Optional[int] = None
    emission_factor: Optional[float] = None
    emission_unit: Optional[str] = None
    data_source: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("", summary="商品マスタ一覧")
def list_products(
    category: Optional[str] = Query(None, description="カテゴリでフィルタ"),
    scope: Optional[int] = Query(None, description="Scope でフィルタ"),
    search: Optional[str] = Query(None, description="商品名で部分一致検索"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """商品マスタの一覧を取得"""
    db = SessionLocal()
    try:
        query = db.query(ProductMaster).filter(ProductMaster.is_active == 1)
        
        if category:
            query = query.filter(ProductMaster.category == category)
        if scope is not None:
            query = query.filter(ProductMaster.scope == scope)
        if search:
            query = query.filter(ProductMaster.product_name.contains(search))
        
        total = query.count()
        products = query.offset(offset).limit(limit).all()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "products": [p.to_dict() for p in products]
        }
    finally:
        db.close()


@router.post("", status_code=201, summary="商品マスタ作成")
def create_product(product: ProductCreate):
    """新しい商品を登録"""
    db = SessionLocal()
    try:
        # 重複チェック
        existing = db.query(ProductMaster).filter(
            ProductMaster.product_code == product.product_code
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"商品コード {product.product_code} は既に存在します")
        
        db_product = ProductMaster(
            product_code=product.product_code,
            product_name=product.product_name,
            category=product.category,
            subcategory=product.subcategory,
            scope=product.scope,
            emission_factor=product.emission_factor,
            emission_unit=product.emission_unit,
            data_source=product.data_source,
            description=product.description,
        )
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        return db_product.to_dict()
    finally:
        db.close()


@router.get("/{product_id}", summary="商品マスタ詳細")
def get_product(product_id: str):
    """商品マスタの詳細を取得"""
    db = SessionLocal()
    try:
        product = db.query(ProductMaster).filter(
            ProductMaster.id == product_id,
            ProductMaster.is_active == 1
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail="商品が見つかりません")
        return product.to_dict()
    finally:
        db.close()


@router.put("/{product_id}", summary="商品マスタ更新")
def update_product(product_id: str, product: ProductUpdate):
    """商品マスタを更新"""
    db = SessionLocal()
    try:
        db_product = db.query(ProductMaster).filter(
            ProductMaster.id == product_id
        ).first()
        if not db_product:
            raise HTTPException(status_code=404, detail="商品が見つかりません")
        
        update_data = product.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_product, field, value)
        
        db_product.updated_at = datetime.now()
        db.commit()
        db.refresh(db_product)
        
        return db_product.to_dict()
    finally:
        db.close()


@router.delete("/{product_id}", summary="商品マスタ削除（論理削除）")
def delete_product(product_id: str):
    """商品マスタを論理削除"""
    db = SessionLocal()
    try:
        db_product = db.query(ProductMaster).filter(
            ProductMaster.id == product_id
        ).first()
        if not db_product:
            raise HTTPException(status_code=404, detail="商品が見つかりません")
        
        db_product.is_active = 0
        db_product.updated_at = datetime.now()
        db.commit()
        
        return {"message": "商品を削除しました", "product_id": product_id}
    finally:
        db.close()


@router.get("/code/{product_code}", summary="商品コードで検索")
def get_product_by_code(product_code: str):
    """商品コードで商品を検索"""
    db = SessionLocal()
    try:
        product = db.query(ProductMaster).filter(
            ProductMaster.product_code == product_code,
            ProductMaster.is_active == 1
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"商品コード {product_code} が見つかりません")
        return product.to_dict()
    finally:
        db.close()


@router.post("/bulk", status_code=201, summary="商品マスタ一括登録")
def bulk_create_products(products: List[ProductCreate]):
    """商品マスタを一括登録"""
    db = SessionLocal()
    try:
        created = []
        for product in products:
            # 重複チェック
            existing = db.query(ProductMaster).filter(
                ProductMaster.product_code == product.product_code
            ).first()
            if existing:
                continue  # スキップ
            
            db_product = ProductMaster(
                product_code=product.product_code,
                product_name=product.product_name,
                category=product.category,
                subcategory=product.subcategory,
                scope=product.scope,
                emission_factor=product.emission_factor,
                emission_unit=product.emission_unit,
                data_source=product.data_source,
                description=product.description,
            )
            db.add(db_product)
            created.append(db_product)
        
        db.commit()
        for p in created:
            db.refresh(p)
        
        return {
            "created_count": len(created),
            "skipped_count": len(products) - len(created),
            "products": [p.to_dict() for p in created]
        }
    finally:
        db.close()
