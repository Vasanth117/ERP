"""Aggregate student statistics for the college admin Student Statistics dashboard."""

from __future__ import annotations

import re
from collections import defaultdict
from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.hostel_admin_models import (
    HOSTEL_BED_HOLDING_ALLOCATION_STATUSES,
    HostelAllocation,
)
from app.modules.college_admin.identity_models import DepartmentStatus, InstitutionDepartment
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AcademicTermSummary,
    DepartmentEnrolmentItem,
    DistributionItem,
    ProgrammeYearMatrixRow,
    StudentStatisticsFilters,
    StudentStatisticsKpiRead,
    StudentStatisticsOverviewRead,
    StudentStatusOverviewItem,
)
from app.modules.college_admin.student_admin_models import (
    AdmissionStatus,
    StudentAdmission,
    StudentLifecycleStatus,
    StudentRecord,
)
from app.modules.hostel.hostel_models import HostelRoomAllocation
from app.modules.students.enums import AcademicStanding
from app.modules.students.models import StudentAcademicRecord, StudentProfile

_reader = OperationalDataReader()

_ENROLLED_LIFECYCLE = frozenset(
    {
        StudentLifecycleStatus.ADMITTED.value,
        StudentLifecycleStatus.ACTIVE.value,
        StudentLifecycleStatus.ON_LEAVE.value,
    }
)

_MATRIX_GROUPS: tuple[tuple[str, str], ...] = (
    ("be_btech", "B.E. / B.Tech"),
    ("bsc", "B.Sc"),
    ("me_mtech", "M.E. / M.Tech"),
    ("mba_mca", "MBA / MCA"),
    ("phd", "Ph.D."),
)

_GENDER_LABELS = {
    "male": "Male",
    "m": "Male",
    "female": "Female",
    "f": "Female",
    "other": "Other / not disclosed",
    "not_disclosed": "Other / not disclosed",
    "prefer_not_to_say": "Other / not disclosed",
}

_CATEGORY_LABELS = {
    "government": "Government quota",
    "government_quota": "Government quota",
    "govt": "Government quota",
    "govt_quota": "Government quota",
    "management": "Management quota",
    "management_quota": "Management quota",
    "mgmt": "Management quota",
    "nri": "NRI / foreign nationals",
    "foreign": "NRI / foreign nationals",
    "nri_foreign": "NRI / foreign nationals",
    "lateral": "Lateral entry",
    "lateral_entry": "Lateral entry",
}


def _academic_year_start(label: str | None) -> int | None:
    if not label:
        return None
    match = re.match(r"^(\d{4})", label.strip())
    return int(match.group(1)) if match else None


def _previous_academic_year_label(label: str) -> str | None:
    start = _academic_year_start(label)
    if start is None:
        return None
    prev_start = start - 1
    end_suffix = start % 100
    return f"{prev_start}-{end_suffix:02d}"


def _batch_start_year(batch_label: str | None) -> int | None:
    if not batch_label:
        return None
    match = re.search(r"(20\d{2})", batch_label)
    return int(match.group(1)) if match else None


def _study_year(batch_label: str | None, academic_year_label: str | None) -> int | None:
    batch_start = _batch_start_year(batch_label)
    ay_start = _academic_year_start(academic_year_label)
    if batch_start is None or ay_start is None:
        return None
    return max(1, min(6, ay_start - batch_start + 1))


def _programme_group_key(programme_code: str | None, programme_name: str | None) -> str:
    code = (programme_code or "").upper()
    name = (programme_name or "").upper()
    blob = f"{code} {name}"
    if "PHD" in blob or "PH.D" in blob or "DOCTOR" in blob:
        return "phd"
    if "MBA" in blob or "MCA" in blob:
        return "mba_mca"
    if re.search(r"\bM\.?E\b|\bM\.?TECH\b|MASTER OF", blob):
        return "me_mtech"
    if "B.SC" in blob or "BSC" in blob or "BACHELOR OF SCIENCE" in blob:
        return "bsc"
    return "be_btech"


def _normalize_meta_key(raw: object) -> str:
    if raw is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", str(raw).strip().lower()).strip("_")


def _meta_lookup(metadata: dict, *keys: str) -> str | None:
    lowered = {str(k).lower(): v for k, v in metadata.items()}
    for key in keys:
        val = lowered.get(key.lower())
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


async def get_student_statistics_overview(
    scope: AccessScope,
    *,
    academic_year_label: str | None = None,
    programme_code: str | None = None,
    study_year: int | None = None,
    department_id: str | None = None,
    campus_id: str | None = None,
) -> StudentStatisticsOverviewRead:
    authorize(scope, Permission.COLLEGE_DASHBOARD_READ)
    tenant_id = require_college_tenant_scope(scope)

    dept_oid = to_object_id(department_id, "department_id") if department_id else None
    campus_oid = to_object_id(campus_id, "campus_id") if campus_id else None

    current_year, current_semester = await _reader.current_academic_term(tenant_id)
    ay_label = academic_year_label or current_year

    departments = await InstitutionDepartment.find(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.status, DepartmentStatus.ACTIVE),
    ).to_list()
    campus_dept_ids: set[PydanticObjectId] | None = None
    if campus_oid is not None:
        campus_dept_ids = {d.id for d in departments if campus_oid in d.campus_ids}
        if not campus_dept_ids:
            campus_dept_ids = {d.id for d in departments if not d.campus_ids}

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog_by_code = {p.programme_code: p for p in programmes}

    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).to_list()
    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    profile_by_user = {p.user_id: p for p in profiles}

    admissions = await StudentAdmission.find(Eq(StudentAdmission.tenant_id, tenant_id)).to_list()
    admission_by_id = {a.id: a for a in admissions}

    academic_records = await StudentAcademicRecord.find(
        Eq(StudentAcademicRecord.tenant_id, tenant_id),
    ).to_list()
    detained_users: set[PydanticObjectId] = set()
    for ar in academic_records:
        if ar.academic_standing in (AcademicStanding.PROBATION, AcademicStanding.SUSPENDED):
            detained_users.add(ar.user_id)

    def record_matches(record: StudentRecord) -> bool:
        if record.department_id and dept_oid and record.department_id != dept_oid:
            return False
        if campus_dept_ids is not None and record.department_id and record.department_id not in campus_dept_ids:
            return False
        if programme_code and (record.programme_code or "").upper() != programme_code.upper():
            return False
        if ay_label:
            admission = admission_by_id.get(record.admission_id) if record.admission_id else None
            if admission and admission.academic_year_code != ay_label:
                return False
            elif not admission and record.batch_label:
                batch_start = _batch_start_year(record.batch_label)
                ay_start = _academic_year_start(ay_label)
                if batch_start is not None and ay_start is not None:
                    max_years = 6
                    if batch_start > ay_start or batch_start < ay_start - max_years + 1:
                        return False
        if study_year is not None:
            computed = _study_year(record.batch_label, ay_label)
            if computed is None or computed != study_year:
                return False
        return True

    # Build canonical student rows (prefer StudentRecord).
    seen_users: set[PydanticObjectId] = set()
    enrolled_rows: list[dict] = []
    discontinued_rows: list[dict] = []

    for record in records:
        if not record_matches(record):
            continue
        seen_users.add(record.user_id)
        profile = profile_by_user.get(record.user_id)
        prog = prog_by_code.get(record.programme_code or "")
        row = {
            "user_id": record.user_id,
            "department_id": record.department_id,
            "programme_code": record.programme_code,
            "programme_name": profile.programme_name if profile else (prog.name if prog else None),
            "batch_label": record.batch_label,
            "lifecycle": record.lifecycle_status.value,
        }
        if record.lifecycle_status in (StudentLifecycleStatus.DISCONTINUED, StudentLifecycleStatus.WITHDRAWN):
            discontinued_rows.append(row)
        elif record.lifecycle_status.value in _ENROLLED_LIFECYCLE:
            enrolled_rows.append(row)

    for profile in profiles:
        if profile.user_id in seen_users:
            continue
        if dept_oid and profile.department_id != dept_oid:
            continue
        if campus_dept_ids is not None and profile.department_id and profile.department_id not in campus_dept_ids:
            continue
        if programme_code and (profile.programme_code or "").upper() != programme_code.upper():
            continue
        if ay_label and profile.batch_label:
            batch_start = _batch_start_year(profile.batch_label)
            ay_start = _academic_year_start(ay_label)
            if batch_start is not None and ay_start is not None:
                max_years = 6
                if batch_start > ay_start or batch_start < ay_start - max_years + 1:
                    continue
        if study_year is not None:
            computed = _study_year(profile.batch_label, ay_label)
            if computed is None or computed != study_year:
                continue
        enrolled_rows.append(
            {
                "user_id": profile.user_id,
                "department_id": profile.department_id,
                "programme_code": profile.programme_code,
                "programme_name": profile.programme_name,
                "batch_label": profile.batch_label,
                "lifecycle": StudentLifecycleStatus.ACTIVE.value,
            }
        )

    total_enrolled = len(enrolled_rows)

    prev_label = _previous_academic_year_label(ay_label) if ay_label else None
    prev_count = 0
    if prev_label:
        prev_count = sum(
            1
            for r in records
            if r.lifecycle_status.value in _ENROLLED_LIFECYCLE
            and (
                (r.admission_id and admission_by_id.get(r.admission_id, None) and admission_by_id[r.admission_id].academic_year_code == prev_label)
                or (_batch_start_year(r.batch_label) == _academic_year_start(prev_label))
            )
        )
    change_pct = None
    if prev_count > 0:
        change_pct = round(((total_enrolled - prev_count) / prev_count) * 100, 1)

    new_admissions = sum(
        1
        for a in admissions
        if a.status == AdmissionStatus.CONFIRMED and (not ay_label or a.academic_year_code == ay_label)
    )
    sanctioned = 0
    for a in admissions:
        if ay_label and a.academic_year_code != ay_label:
            continue
        intake = a.metadata.get("sanctioned_intake") or a.metadata.get("intake")
        if isinstance(intake, (int, float)):
            sanctioned += int(intake)
    intake_fill_pct = round((new_admissions / sanctioned) * 100, 1) if sanctioned > 0 else None

    hostel_user_ids: set[PydanticObjectId] = set()
    for alloc in await HostelRoomAllocation.find(Eq(HostelRoomAllocation.tenant_id, tenant_id)).to_list():
        hostel_user_ids.add(alloc.student_user_id)
    active_statuses = list(HOSTEL_BED_HOLDING_ALLOCATION_STATUSES)
    for alloc in await HostelAllocation.find(
        Eq(HostelAllocation.tenant_id, tenant_id),
        In(HostelAllocation.status, active_statuses),
    ).to_list():
        hostel_user_ids.add(alloc.student_user_id)

    enrolled_user_ids = {r["user_id"] for r in enrolled_rows}
    hostel_residents = len(hostel_user_ids & enrolled_user_ids)
    hostel_pct = round((hostel_residents / total_enrolled) * 100, 1) if total_enrolled else None

    discontinued = len(discontinued_rows)
    disc_pct = round((discontinued / total_enrolled) * 100, 2) if total_enrolled else None

    dept_counts: dict[str, int] = defaultdict(int)
    for row in enrolled_rows:
        if row["department_id"] is None:
            dept_counts["__unassigned__"] += 1
        else:
            dept_counts[str(row["department_id"])] += 1

    enrolment_by_department: list[DepartmentEnrolmentItem] = []
    for dept in departments:
        count = dept_counts.get(str(dept.id), 0)
        if count == 0 and dept_oid is not None and dept.id != dept_oid:
            continue
        enrolment_by_department.append(
            DepartmentEnrolmentItem(
                department_id=str(dept.id),
                department_code=dept.department_code,
                department_name=dept.name,
                student_count=count,
            )
        )
    if dept_counts.get("__unassigned__"):
        enrolment_by_department.append(
            DepartmentEnrolmentItem(
                department_id=None,
                department_code="UNASSIGNED",
                department_name="Unassigned",
                student_count=dept_counts["__unassigned__"],
            )
        )
    enrolment_by_department.sort(key=lambda x: x.student_count, reverse=True)

    matrix: dict[str, dict[str, int]] = {key: defaultdict(int) for key, _ in _MATRIX_GROUPS}
    for row in enrolled_rows:
        group = _programme_group_key(row["programme_code"], row["programme_name"])
        year = _study_year(row["batch_label"], ay_label) or 1
        year_key = f"year_{min(year, 4)}"
        matrix[group][year_key] += 1
        matrix[group]["total"] += 1

    programme_year_matrix = [
        ProgrammeYearMatrixRow(
            group_key=key,
            label=label,
            year_1=matrix[key].get("year_1", 0),
            year_2=matrix[key].get("year_2", 0),
            year_3=matrix[key].get("year_3", 0),
            year_4=matrix[key].get("year_4", 0),
            total=matrix[key].get("total", 0),
        )
        for key, label in _MATRIX_GROUPS
        if matrix[key].get("total", 0) > 0 or not enrolled_rows
    ]

    gender_counts: dict[str, int] = defaultdict(int)
    category_counts: dict[str, int] = defaultdict(int)
    for admission in admissions:
        if ay_label and admission.academic_year_code != ay_label:
            continue
        if admission.status != AdmissionStatus.CONFIRMED:
            continue
        gender_raw = _meta_lookup(admission.metadata, "gender", "sex")
        if gender_raw:
            gkey = _normalize_meta_key(gender_raw)
            label = _GENDER_LABELS.get(gkey, gender_raw.title())
            gender_counts[label] += 1
        cat_raw = _meta_lookup(
            admission.metadata,
            "admission_category",
            "category",
            "quota",
            "quota_type",
        )
        if cat_raw:
            ckey = _normalize_meta_key(cat_raw)
            label = _CATEGORY_LABELS.get(ckey, cat_raw.replace("_", " ").title())
            category_counts[label] += 1

    def _distribution(counts: dict[str, int]) -> list[DistributionItem]:
        total = sum(counts.values())
        items = []
        for label, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            share = round((count / total) * 100, 1) if total else None
            items.append(DistributionItem(key=_normalize_meta_key(label), label=label, count=count, share_pct=share))
        return items

    gender_distribution = _distribution(gender_counts)
    admission_category = _distribution(category_counts)

    status_active = sum(1 for r in enrolled_rows if r["lifecycle"] == StudentLifecycleStatus.ACTIVE.value)
    status_leave = sum(1 for r in enrolled_rows if r["lifecycle"] == StudentLifecycleStatus.ON_LEAVE.value)
    status_detained = len({r["user_id"] for r in enrolled_rows if r["user_id"] in detained_users})
    status_discontinued = discontinued

    student_status = [
        StudentStatusOverviewItem(
            status_key="active",
            label="Active",
            description="Attending regular classes",
            count=status_active,
        ),
        StudentStatusOverviewItem(
            status_key="on_leave",
            label="On academic leave",
            description="Medical / personal",
            count=status_leave,
        ),
        StudentStatusOverviewItem(
            status_key="detained",
            label="Year back / detained",
            description="Attendance or credit shortage",
            count=status_detained,
        ),
        StudentStatusOverviewItem(
            status_key="discontinued",
            label="Discontinued",
            description="Withdrawn this academic year",
            count=status_discontinued,
        ),
    ]

    matrix_total = sum(r.total for r in programme_year_matrix)
    group_count = sum(1 for r in programme_year_matrix if r.total > 0)

    return StudentStatisticsOverviewRead(
        filters=StudentStatisticsFilters(
            academic_year_label=ay_label,
            programme_code=programme_code,
            study_year=study_year,
            department_id=department_id,
            campus_id=campus_id,
        ),
        academic_term=AcademicTermSummary(academic_year_label=current_year, semester_label=current_semester),
        kpis=StudentStatisticsKpiRead(
            total_enrolled=total_enrolled,
            total_enrolled_change_pct=change_pct,
            total_enrolled_change_reference_year=prev_label,
            new_admissions=new_admissions,
            new_admissions_intake_sanctioned=sanctioned or None,
            new_admissions_intake_fill_pct=intake_fill_pct,
            hostel_residents=hostel_residents,
            hostel_residents_pct_of_enrolled=hostel_pct,
            discontinued=discontinued,
            discontinued_pct_of_enrolled=disc_pct,
            discontinued_this_semester=None,
        ),
        enrolment_by_department=enrolment_by_department,
        programme_year_matrix=programme_year_matrix,
        programme_matrix_student_total=matrix_total,
        programme_matrix_group_count=group_count,
        gender_distribution=gender_distribution,
        admission_category=admission_category,
        student_status=student_status,
        generated_at=utcnow(),
    )