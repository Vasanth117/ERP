"""Aggregate HR report datasets (no duplicate operational stores)."""

from datetime import date

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.hr.attendance_schedule_models import HrEmployeeAttendanceMonthlySummary
from app.modules.hr.benefits_models import EmployeeBenefitClaim
from app.modules.hr.employee_profile_models import HrEmployeeProfile
from app.modules.hr.enums import HrBenefitClaimStatus, HrPerformanceReviewStatus, HrTrainingEnrollmentStatus
from app.modules.hr.leave_models import HrLeaveBalance
from app.modules.hr.onboarding_models import HrOnboardingProcess
from app.modules.hr.payroll_models import HrEmployeePayrollRecord, HrPayrollRun
from app.modules.hr.performance_models import EmployeePerformanceReview
from app.modules.hr.recruitment_models import HrJobApplication
from app.modules.hr.statutory_tax_models import EmployeeTaxDeclaration
from app.modules.hr.training_models import HrTrainingEnrollment
from app.modules.tenants.models import Department


class HrReportsRepository:
    async def build(self, tenant_id: PydanticObjectId, report_key: str, filters: dict) -> tuple[list[dict], dict]:
        if report_key == "employee_master":
            return await self._employee_master(tenant_id, filters)
        if report_key == "department_employees":
            return await self._department_employees(tenant_id, filters)
        if report_key == "leave_summary":
            return await self._leave_summary(tenant_id, filters)
        if report_key == "attendance_monthly":
            return await self._attendance_monthly(tenant_id, filters)
        if report_key == "payroll_summary":
            return await self._payroll_summary(tenant_id, filters)
        if report_key == "benefits_claims":
            return await self._benefits_claims(tenant_id, filters)
        if report_key == "tax_declaration_status":
            return await self._tax_declarations(tenant_id, filters)
        if report_key == "performance_reviews":
            return await self._performance_reviews(tenant_id, filters)
        if report_key == "training_completion":
            return await self._training_completion(tenant_id, filters)
        if report_key == "recruitment_pipeline":
            return await self._recruitment_pipeline(tenant_id, filters)
        if report_key == "onboarding_status":
            return await self._onboarding_status(tenant_id, filters)
        return [], {"error": "unknown_report"}

    async def _employee_master(self, tenant_id: PydanticObjectId, filters: dict) -> tuple[list[dict], dict]:
        rows = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
        out = []
        for emp in rows:
            if filters.get("department_id") and str(emp.department_id) != str(filters["department_id"]):
                continue
            profile = await HrEmployeeProfile.find_one(
                Eq(HrEmployeeProfile.tenant_id, tenant_id),
                Eq(HrEmployeeProfile.user_id, emp.user_id),
            )
            out.append(
                {
                    "employee_code": profile.employee_code if profile else emp.employee_id,
                    "user_id": str(emp.user_id),
                    "designation": emp.designation,
                    "department_id": str(emp.department_id) if emp.department_id else "",
                    "employment_status": emp.employment_status.value,
                    "joining_date": (emp.confidential_hr or {}).get("joining_date", ""),
                }
            )
        return out, {"total": len(out)}

    async def _department_employees(self, tenant_id: PydanticObjectId, filters: dict) -> tuple[list[dict], dict]:
        rows, _ = await self._employee_master(tenant_id, filters)
        groups: dict[str, int] = {}
        for r in rows:
            dept = r.get("department_id") or "unassigned"
            groups[dept] = groups.get(dept, 0) + 1
        out = [{"department_id": k, "employee_count": v} for k, v in sorted(groups.items())]
        return out, {"departments": len(out)}

    async def _leave_summary(self, tenant_id: PydanticObjectId, filters: dict) -> tuple[list[dict], dict]:
        year = int(filters.get("period_year", date.today().year))
        balances = await HrLeaveBalance.find(
            Eq(HrLeaveBalance.tenant_id, tenant_id),
            Eq(HrLeaveBalance.period_year, year),
        ).to_list()
        out = [
            {
                "employee_user_id": str(b.employee_user_id),
                "leave_type": b.leave_type,
                "available": str(b.available),
                "used": str(b.used),
            }
            for b in balances
        ]
        return out, {"period_year": year, "rows": len(out)}

    async def _attendance_monthly(self, tenant_id: PydanticObjectId, filters: dict) -> tuple[list[dict], dict]:
        year = int(filters.get("period_year", date.today().year))
        month = int(filters.get("period_month", date.today().month))
        rows = await HrEmployeeAttendanceMonthlySummary.find(
            Eq(HrEmployeeAttendanceMonthlySummary.tenant_id, tenant_id),
            Eq(HrEmployeeAttendanceMonthlySummary.period_year, year),
            Eq(HrEmployeeAttendanceMonthlySummary.period_month, month),
        ).to_list()
        out = [
            {
                "employee_user_id": str(r.employee_user_id),
                "present_days": r.present_days,
                "absent_days": r.absent_days,
                "status": r.status.value,
            }
            for r in rows
        ]
        return out, {"period_year": year, "period_month": month}

    async def _payroll_summary(self, tenant_id: PydanticObjectId, filters: dict) -> tuple[list[dict], dict]:
        runs = await HrPayrollRun.find(Eq(HrPayrollRun.tenant_id, tenant_id)).sort(-HrPayrollRun.created_at).limit(5).to_list()
        if not runs:
            return [], {"runs": 0}
        run = runs[0]
        recs = await HrEmployeePayrollRecord.find(
            Eq(HrEmployeePayrollRecord.tenant_id, tenant_id),
            Eq(HrEmployeePayrollRecord.payroll_run_id, run.id),
        ).to_list()
        out = [
            {
                "employee_user_id": str(r.employee_user_id),
                "gross_salary": r.gross_salary,
                "net_payable": r.net_payable,
                "payment_status": r.payment_status,
            }
            for r in recs
            if not r.exclusion_reason
        ]
        return out, {"run_code": run.run_code, "run_status": run.status.value}

    async def _benefits_claims(self, tenant_id: PydanticObjectId, filters: dict) -> tuple[list[dict], dict]:
        rows = await EmployeeBenefitClaim.find(Eq(EmployeeBenefitClaim.tenant_id, tenant_id)).to_list()
        out = [
            {
                "claim_code": c.claim_code,
                "category": c.claim_category,
                "status": c.status.value,
                "requested_amount": c.requested_amount,
                "approved_amount": c.approved_amount,
                "payment_status": c.payment_status,
            }
            for c in rows
            if not filters.get("status") or c.status.value == filters["status"]
        ]
        pending = sum(1 for c in rows if c.status == HrBenefitClaimStatus.AWAITING_REVIEW)
        return out, {"pending_claims": pending}

    async def _tax_declarations(self, tenant_id: PydanticObjectId, filters: dict) -> tuple[list[dict], dict]:
        rows = await EmployeeTaxDeclaration.find(Eq(EmployeeTaxDeclaration.tenant_id, tenant_id)).to_list()
        out = [
            {
                "employee_user_id": str(d.employee_user_id),
                "fy_code": d.fy_code,
                "status": d.status.value,
                "regime_code": d.regime_code,
            }
            for d in rows
        ]
        return out, {"total": len(out)}

    async def _performance_reviews(self, tenant_id: PydanticObjectId, filters: dict) -> tuple[list[dict], dict]:
        rows = await EmployeePerformanceReview.find(Eq(EmployeePerformanceReview.tenant_id, tenant_id)).to_list()
        out = [
            {
                "employee_user_id": str(r.employee_user_id),
                "status": r.status.value,
                "overall_rating": r.overall_rating or "",
            }
            for r in rows
        ]
        pending_self = sum(1 for r in rows if r.status == HrPerformanceReviewStatus.SELF_ASSESSMENT)
        return out, {"pending_self_assessment": pending_self}

    async def _training_completion(self, tenant_id: PydanticObjectId, filters: dict) -> tuple[list[dict], dict]:
        rows = await HrTrainingEnrollment.find(Eq(HrTrainingEnrollment.tenant_id, tenant_id)).to_list()
        out = [
            {
                "employee_user_id": str(r.employee_user_id),
                "program_code": r.program_code,
                "status": r.status.value,
                "certificate_issued": r.certificate_issued,
            }
            for r in rows
        ]
        completed = sum(1 for r in rows if r.status == HrTrainingEnrollmentStatus.COMPLETED)
        return out, {"completed": completed}

    async def _recruitment_pipeline(self, tenant_id: PydanticObjectId, filters: dict) -> tuple[list[dict], dict]:
        apps = await HrJobApplication.find(Eq(HrJobApplication.tenant_id, tenant_id)).limit(500).to_list()
        stages: dict[str, int] = {}
        for a in apps:
            stage = a.stage.value if hasattr(a.stage, "value") else str(a.stage)
            stages[stage] = stages.get(stage, 0) + 1
        out = [{"stage": k, "count": v} for k, v in sorted(stages.items())]
        return out, {"applications": len(apps)}

    async def _onboarding_status(self, tenant_id: PydanticObjectId, filters: dict) -> tuple[list[dict], dict]:
        rows = await HrOnboardingProcess.find(Eq(HrOnboardingProcess.tenant_id, tenant_id)).to_list()
        out = [
            {
                "employee_user_id": str(r.employee_user_id) if r.employee_user_id else "",
                "status": r.status.value,
            }
            for r in rows
        ]
        return out, {"total": len(out)}