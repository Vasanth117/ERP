"""Versioned API routes."""

from fastapi import APIRouter

from app import __version__
from app.modules.academics.router import router as academics_router
from app.modules.attendance.router import router as attendance_router
from app.modules.audit.router import router as audit_router
from app.modules.college_admin.router import router as college_admin_router
from app.modules.auth.router import router as auth_router
from app.modules.examinations.router import router as examinations_router
from app.modules.faculty.router import router as faculty_router
from app.modules.finance.router import router as finance_router
from app.modules.hostel.router import router as hostel_router
from app.modules.transport.router import router as transport_router
from app.modules.hr.router import router as hr_router
from app.modules.library.router import router as library_router
from app.modules.students.router import router as students_router
from app.modules.platform.router import router as platform_router
from app.modules.tenants.router import router as tenants_router
from app.modules.users.router import router as users_router

api_router = APIRouter()

ACTIVE_MODULES = ["auth", "tenants", "platform", "configuration", "users", "audit", "college_admin", "faculty", "students"]
PLANNED_MODULES = [
    "academics",
    "attendance",
    "examinations",
    "finance",
    "hr",
    "library",
    "hostel",
]


@api_router.get("", tags=["meta"])
def api_index() -> dict:
    return {
        "name": "ERP System API",
        "version": __version__,
        "modules": [
            *[{"name": name, "status": "active"} for name in ACTIVE_MODULES],
            *[{"name": name, "status": "planned"} for name in PLANNED_MODULES],
        ],
        "docs": "/docs",
    }


api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants_router, prefix="/tenants", tags=["tenants"])
api_router.include_router(platform_router, prefix="/platform", tags=["platform"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(audit_router, prefix="/audit", tags=["audit"])
api_router.include_router(college_admin_router, prefix="/college-admin", tags=["college-admin"])
api_router.include_router(academics_router, prefix="/academics", tags=["academics"])
api_router.include_router(students_router, prefix="/students", tags=["students"])
api_router.include_router(faculty_router, prefix="/faculty", tags=["faculty"])
api_router.include_router(attendance_router, prefix="/attendance", tags=["attendance"])
api_router.include_router(examinations_router, prefix="/examinations", tags=["examinations"])
api_router.include_router(finance_router, prefix="/finance", tags=["finance"])
api_router.include_router(hr_router, prefix="/hr", tags=["hr"])
api_router.include_router(library_router, prefix="/library", tags=["library"])
api_router.include_router(hostel_router, prefix="/hostel", tags=["hostel"])
api_router.include_router(transport_router, prefix="/transport", tags=["transport"])
