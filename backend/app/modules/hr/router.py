"""HR staff portal module."""

from fastapi import APIRouter

from app.modules.hr.dashboard_router import router as dashboard_router
from app.modules.hr.document_router import router as document_router
from app.modules.hr.employee_profile_router import router as employee_profile_router
from app.modules.hr.organization_router import router as organization_router
from app.modules.hr.attendance_schedule_router import router as attendance_schedule_router
from app.modules.hr.employment_change_router import router as employment_change_router
from app.modules.hr.salary_structure_router import router as salary_structure_router
from app.modules.hr.leave_router import router as leave_router
from app.modules.hr.offboarding_router import router as offboarding_router
from app.modules.hr.onboarding_router import router as onboarding_router
from app.modules.hr.payroll_router import router as payroll_router
from app.modules.hr.payslip_router import router as payslip_router
from app.modules.hr.recruitment_router import router as recruitment_router
from app.modules.hr.statutory_tax_router import router as statutory_tax_router
from app.modules.hr.employee_self_service_router import router as employee_self_service_router
from app.modules.hr.benefits_router import router as benefits_router
from app.modules.hr.performance_router import router as performance_router
from app.modules.hr.training_router import router as training_router
from app.modules.hr.hr_communication_router import router as hr_communication_router
from app.modules.hr.hr_reports_router import router as hr_reports_router
from app.modules.hr.hr_settings_router import router as hr_settings_router
from app.modules.hr.hr_audit_router import router as hr_audit_router

router = APIRouter()
router.include_router(dashboard_router)
router.include_router(employee_profile_router)
router.include_router(organization_router)
router.include_router(document_router)
router.include_router(recruitment_router)
router.include_router(onboarding_router)
router.include_router(employment_change_router)
router.include_router(offboarding_router)
router.include_router(leave_router)
router.include_router(attendance_schedule_router)
router.include_router(salary_structure_router)
router.include_router(payroll_router)
router.include_router(payslip_router)
router.include_router(statutory_tax_router)
router.include_router(employee_self_service_router)
router.include_router(benefits_router)
router.include_router(performance_router)
router.include_router(training_router)
router.include_router(hr_communication_router)
router.include_router(hr_reports_router)
router.include_router(hr_settings_router)
router.include_router(hr_audit_router)