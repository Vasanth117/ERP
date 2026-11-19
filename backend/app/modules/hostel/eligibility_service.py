"""Hostel application eligibility (tenant-configurable)."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.roles import Role
from app.modules.auth.models import User
from app.modules.college_admin.models import InstitutionSettings
from app.modules.hostel.infrastructure_models import InstitutionHostel
from app.modules.students.enums import StudentEnrollmentStatus
from app.modules.students.models import StudentAcademicRecord, StudentProfile


async def load_hostel_eligibility_rules(tenant_id: PydanticObjectId) -> dict:
    settings = await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))
    if not settings:
        return {}
    hostel_cfg = settings.settings.get("hostel") or {}
    return hostel_cfg.get("eligibility_rules") or {}


async def evaluate_hostel_eligibility(
    tenant_id: PydanticObjectId,
    *,
    student_user: User,
    profile: StudentProfile | None,
    academic_year_label: str,
    preferred_hostel_code: str | None,
    eligibility_payload: dict | None = None,
) -> dict:
    rules = await load_hostel_eligibility_rules(tenant_id)
    payload = eligibility_payload or {}
    issues: list[str] = []
    if student_user.tenant_id != tenant_id:
        issues.append("student_tenant_mismatch")
    if student_user.role != Role.STUDENT:
        issues.append("not_a_student")
    if profile is None:
        issues.append("student_profile_missing")
    record = await StudentAcademicRecord.find_one(
        Eq(StudentAcademicRecord.tenant_id, tenant_id),
        Eq(StudentAcademicRecord.user_id, student_user.id),
    )
    if record and record.enrollment_status != StudentEnrollmentStatus.ACTIVE:
        if rules.get("require_active_enrollment", True):
            issues.append("enrollment_not_active")
    elif rules.get("require_active_enrollment", True) and record is None:
        issues.append("academic_record_missing")
    allowed_years = rules.get("allowed_academic_years")
    if isinstance(allowed_years, list) and allowed_years and academic_year_label not in allowed_years:
        issues.append("academic_year_not_eligible")
    if preferred_hostel_code:
        hostel = await InstitutionHostel.find_one(
            Eq(InstitutionHostel.tenant_id, tenant_id),
            Eq(InstitutionHostel.hostel_code, preferred_hostel_code.strip().upper()),
        )
        if hostel is None or not hostel.is_active:
            issues.append("preferred_hostel_unavailable")
        disallowed = {str(x).upper() for x in rules.get("disallowed_hostel_codes", [])}
        if preferred_hostel_code.upper() in disallowed:
            issues.append("hostel_not_allowed")
    min_distance_km = rules.get("minimum_distance_km_for_hostel")
    if min_distance_km is not None:
        distance = payload.get("distance_km")
        if distance is not None and float(distance) < float(min_distance_km):
            issues.append("distance_criteria_not_met")
    gender_map = rules.get("gender_hostel_map") or {}
    student_gender = payload.get("gender")
    if gender_map and student_gender and preferred_hostel_code:
        allowed = gender_map.get(student_gender, [])
        if allowed and preferred_hostel_code.upper() not in {str(c).upper() for c in allowed}:
            issues.append("gender_hostel_mismatch")
    return {
        "eligible": len(issues) == 0,
        "issues": issues,
        "rules_version": rules.get("version", "default"),
        "academic_year_label": academic_year_label,
    }