"""SQLAlchemy base and table definitions."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer,
    JSON, String, Text, func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def new_uuid() -> str:
    return str(uuid.uuid4())


class DataUpload(Base):
    """CSVアップロード管理テーブル"""
    __tablename__ = "data_uploads"

    id = Column(String(36), primary_key=True, default=new_uuid)
    filename = Column(String(255), nullable=False)
    data_type = Column(String(50), nullable=False)  # "accounting"|"sales"|"pos"
    row_count = Column(Integer, default=0)
    status = Column(String(50), default="pending_mapping")
    created_at = Column(DateTime, default=func.now())
    deleted_at = Column(DateTime, nullable=True)

    rows = relationship("UploadRow", back_populates="upload")
    mappings = relationship("ColumnMapping", back_populates="upload")
    jobs = relationship("CalculationJob", back_populates="upload")


class UploadRow(Base):
    """アップロードデータの行"""
    __tablename__ = "upload_rows"

    id = Column(String(36), primary_key=True, default=new_uuid)
    upload_id = Column(String(36), ForeignKey("data_uploads.id"), nullable=False)
    row_index = Column(Integer, nullable=False)
    raw_data = Column(JSON, nullable=False)   # 元のCSV行データ
    mapped_data = Column(JSON, nullable=True) # マッピング適用後

    upload = relationship("DataUpload", back_populates="rows")


class ColumnMapping(Base):
    """列マッピング設定"""
    __tablename__ = "column_mappings"

    id = Column(String(36), primary_key=True, default=new_uuid)
    upload_id = Column(String(36), ForeignKey("data_uploads.id"), nullable=False)
    mappings = Column(JSON, nullable=False)  # {"元列名": "標準列名", ...}
    created_at = Column(DateTime, default=func.now())

    upload = relationship("DataUpload", back_populates="mappings")


class EmissionFactorVersion(Base):
    """排出係数バージョン管理"""
    __tablename__ = "emission_factor_versions"

    id = Column(String(36), primary_key=True, default=new_uuid)
    version = Column(String(20), unique=True, nullable=False)  # "2023"
    description = Column(Text, nullable=True)
    is_latest = Column(Integer, default=0)  # 1=latest
    published_at = Column(DateTime, nullable=True)


class CalculationJob(Base):
    """算出ジョブ"""
    __tablename__ = "calculation_jobs"

    id = Column(String(36), primary_key=True, default=new_uuid)
    upload_id = Column(String(36), ForeignKey("data_uploads.id"), nullable=False)
    emission_factor_version = Column(String(20), default="2023")
    status = Column(String(50), default="pending")  # pending|running|completed|failed
    parent_job_id = Column(String(36), nullable=True)  # 再計算の場合
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    upload = relationship("DataUpload", back_populates="jobs")
    results = relationship("CalculationResult", back_populates="job")
    scope_summary = relationship("ScopeSummary", back_populates="job", uselist=False)


class CalculationResult(Base):
    """算出結果（行レベル）"""
    __tablename__ = "calculation_results"

    id = Column(String(36), primary_key=True, default=new_uuid)
    job_id = Column(String(36), ForeignKey("calculation_jobs.id"), nullable=False)
    row_index = Column(Integer, nullable=False)
    activity_type = Column(String(100), nullable=True)
    scope = Column(Integer, nullable=True)
    activity_amount = Column(Float, nullable=True)
    activity_unit = Column(String(50), nullable=True)
    emission_factor_value = Column(Float, nullable=True)
    amount_kg_co2e = Column(Float, nullable=True)
    status = Column(String(50), default="calculated")  # calculated|unclassified|error
    error_message = Column(Text, nullable=True)

    job = relationship("CalculationJob", back_populates="results")


class ScopeSummary(Base):
    """Scope別集計（ジョブレベル）"""
    __tablename__ = "scope_summaries"

    id = Column(String(36), primary_key=True, default=new_uuid)
    job_id = Column(String(36), ForeignKey("calculation_jobs.id"), unique=True, nullable=False)
    scope1_total = Column(Float, default=0.0)
    scope2_total = Column(Float, default=0.0)
    scope3_total = Column(Float, default=0.0)
    grand_total = Column(Float, default=0.0)
    total_row_count = Column(Integer, default=0)
    calculated_row_count = Column(Integer, default=0)
    unclassified_count = Column(Integer, default=0)

    job = relationship("CalculationJob", back_populates="scope_summary")


class AuditLog(Base):
    """監査ログ"""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=new_uuid)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(36), nullable=True)
    actor_id = Column(String(100), default="system")
    detail = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())


class User(Base):
    """ユーザー管理テーブル"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=new_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user")  # "admin" | "user"
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ProductMaster(Base):
    """商品マスタ - 商品別の排出係数管理"""
    __tablename__ = "product_master"

    id = Column(String(36), primary_key=True, default=new_uuid)
    product_code = Column(String(50), unique=True, nullable=False, index=True)  # SKU
    product_name = Column(String(255), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # 飲料/食品/繊維/電子/その他
    subcategory = Column(String(50), nullable=True)  # 詳細カテゴリ
    scope = Column(Integer, nullable=False, index=True)  # 1, 2, 3
    emission_factor = Column(Float, nullable=False)  # kg-CO2e/単位
    emission_unit = Column(String(50), nullable=False)  # "個"/"円"/"kg"/"L"
    data_source = Column(String(100), nullable=True)  # "環境省 2023"/"IDEA v3"/"自社計算"
    description = Column(Text, nullable=True)  # 詳細説明
    is_active = Column(Integer, default=1)  # 1=有効，0=無効
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "category": self.category,
            "subcategory": self.subcategory,
            "scope": self.scope,
            "emission_factor": self.emission_factor,
            "emission_unit": self.emission_unit,
            "data_source": self.data_source,
            "description": self.description,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
