"""Student eligibility and structure resolution for fee assessment."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.modules.accounts_finance.enums import FeeStructureLifecycleStatus
from app.modules.accounts_finance.models import FinanceFeeStructure, FinanceFeeStructureComponent
from app.modules.college_admin.finance_admin_models import StudentFeeAssessment
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentRecord
from app.modules.students.enums import StudentEnrollmentStatus
from app.modules.students.models import StudentAcademicRecord, StudentProfile


async def eligible_students(
    tenant_id: PydanticObjectId,
    *,
    academic_year_label: str,
    semester_label: str,
    programme_code: str | None = None,
    department_id: PydanticObjectId | None = None,
    batch_label: str | None = None,
    campus_id: PydanticObjectId | None = None,
) -> list[StudentRecord]:
    query = {
        "tenant_id": tenant_id,
        "lifecycle_status": StudentLifecycleStatus.ACTIVE,
        "enrollment_status": StudentEnrollmentStatus.ACTIVE,
    }
    if programme_code:
        query["programme_code"] = programme_code.upper()
    if department_id:
        query["department_id"] = department_id
    if batch_label:
        query["batch_label"] = batch_label
    records = await StudentRecord.find(query).to_list()
    if not records:
        return []
    user_ids = [r.user_id for r in records]
    academic = await StudentAcademicRecord.find(
        Eq(StudentAcademicRecord.tenant_id, tenant_id),
        In(StudentAcademicRecord.user_id, user_ids),
        Eq(StudentAcademicRecord.academic_year_label, academic_year_label),
        Eq(StudentAcademicRecord.semester_label, semester_label),
        Eq(StudentAcademicRecord.enrollment_status, StudentEnrollmentStatus.ACTIVE),
    ).to_list()
    active_ids = {a.user_id for a in academic}
    filtered = [r for r in records if r.user_id in active_ids]
    if campus_id:
        profiles = await StudentProfile.find(
            Eq(StudentProfile.tenant_id, tenant_id),
            In(StudentProfile.user_id, [r.user_id for r in filtered]),
        ).to_list()
        # campus not on profile — skip campus filter when absent
        _ = campus_id
    return filtered if academic else records


async def resolve_active_structure(
    tenant_id: PydanticObjectId,
    *,
    programme_code: str,
    academic_year_label: str,
    semester_label: str,
    batch_year: str | None = None,
    campus_id: PydanticObjectId | None = None,
    student_category: str | None = None,
) -> FinanceFeeStructure | None:
    structures = await FinanceFeeStructure.find(
        Eq(FinanceFeeStructure.tenant_id, tenant_id),
        Eq(FinanceFeeStructure.programme_code, programme_code.upper()),
        Eq(FinanceFeeStructure.academic_year_label, academic_year_label),
        Eq(FinanceFeeStructure.semester_label, semester_label),
        Eq(FinanceFeeStructure.status, FeeStructureLifecycleStatus.ACTIVE),
    ).to_list()
    if not structures:
        return None
    for s in structures:
        if batch_year and s.batch_year and s.batch_year != batch_year:
            continue
        if campus_id and s.campus_id and s.campus_id != campus_id:
            continue
        if student_category and s.student_category and s.student_category != student_category:
            continue
        return s
    return structures[0]


async def load_structure_components(tenant_id: PydanticObjectId, structure_id: str) -> list[FinanceFeeStructureComponent]:
    return await FinanceFeeStructureComponent.find(
        Eq(FinanceFeeStructureComponent.tenant_id, tenant_id),
        Eq(FinanceFeeStructureComponent.structure_id, structure_id),
    ).to_list()


async def has_duplicate_assessment(
    tenant_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    academic_year_label: str,
    semester_label: str,
    structure_id: str,
) -> bool:
    blocking = {"draft", "in_review", "approved", "posted"}
    row = await StudentFeeAssessment.find_one(
        Eq(StudentFeeAssessment.tenant_id, tenant_id),
        Eq(StudentFeeAssessment.student_user_id, student_user_id),
        Eq(StudentFeeAssessment.academic_year_label, academic_year_label),
        Eq(StudentFeeAssessment.semester_label, semester_label),
        Eq(StudentFeeAssessment.structure_id, structure_id),
        In(StudentFeeAssessment.workflow_status, list(blocking)),
    )
    return row is not None