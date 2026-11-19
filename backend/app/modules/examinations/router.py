"""Examinations module — examination cell (phase 1) and future domain routes."""

from fastapi import APIRouter

from app.modules.examinations.exam_cell_router import router as exam_cell_router

router = APIRouter()
router.include_router(exam_cell_router, prefix="/cell", tags=["examination-cell"])