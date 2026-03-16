"""API v1 router."""
from fastapi import APIRouter
from app.api.v1 import uploads, calculations, reports, comparisons, factors, audit, dashboard, products, pos_calculations, pdf_reports

router = APIRouter()
router.include_router(uploads.router,         prefix="/uploads",         tags=["uploads"])
router.include_router(calculations.router,    prefix="/calculations",    tags=["calculations"])
router.include_router(reports.router,         prefix="/reports",         tags=["reports"])
router.include_router(comparisons.router,     prefix="/comparisons",     tags=["comparisons"])
router.include_router(factors.router,         prefix="/factors",         tags=["factors"])
router.include_router(audit.router,           prefix="/audit-logs",      tags=["audit"])
router.include_router(dashboard.router,       prefix="/dashboard",       tags=["dashboard"])
router.include_router(products.router,        prefix="/products",        tags=["products"])
router.include_router(pos_calculations.router, prefix="/pos",            tags=["pos"])
router.include_router(pdf_reports.router,     prefix="/pdf",             tags=["pdf"])
