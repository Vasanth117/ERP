"""Student promotion management page (CA 06 — Promotion tab)."""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date, timedelta

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.attendance.enums import AttendanceMarkStatus
from app.modules.attendance.models import AttendancePolicyReference, AttendanceRecord
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme, AcademicRegulation, AcademicRegulationCatalog, AcademicYear
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    StudentAdminDashboardFilterOption,
    StudentPromotionManagementPageRead,
    StudentPromotionPromotePayload,
    StudentPromotionRuleRow,
    UserDashboardKpi,
)
from app.modules.college_admin.student_admin_models import StudentLifecycleStatus, StudentPromotionRecord, StudentRecord
from app.modules.college_admin.student_administration_dashboard_page_service import _fmt_time_label
from app.modules.college_admin.student_statistics_overview_service import _study_year
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.students.arrear_backlog_enums import BacklogStatus
from app.modules.students.arrear_backlog_models import StudentArrearReference
from app.modules.students.enums import AcademicStanding, ProgressionStatus
from app.modules.students.models import StudentAcademicRecord

_reader = OperationalDataReader()
_SCOPE_KEY = "student_promotion"
_DEFAULT_RULES = {
    "min_attendance_pct": "75",
    "max_arrears": "4",
    "fee_due_grace_days": "30",
    "regulation_code": "R2022",
}

_PRESENT = frozenset(
    {
        AttendanceMarkStatus.PRESENT,
        AttendanceMarkStatus.LATE,
        AttendanceMarkStatus.EXCUSED,
    }
)

_ELIGIBLE_LIFECYCLE = frozenset(
    {
        StudentLifecycleStatus.ACTIVE,
        StudentLifecycleStatus.ADMITTED,
    }
)


def _ay_display(code: str) -> str:
    return code.replace("-", "–") if code else "—"


def _transition_key(from_ay: str, from_sem: str, to_ay: str, to_sem: str) -> str:
    return f"{from_ay}::{from_sem}::{to_ay}::{to_sem}"


def _parse_transition_key(key: str | None, default_parts: tuple[str, str, str, str]) -> tuple[str, str, str, str]:
    if key and key.count("::") == 3:
        return tuple(key.split("::", 3))  # type: ignore[return-value]
    return default_parts


def _transition_label(from_ay: str, from_sem: str, to_ay: str, to_sem: str) -> str:
    return f"{from_sem} {_ay_display(from_ay)} to {to_sem} {_ay_display(to_ay)}"


def _infer_next_term(from_ay: str, from_sem: str) -> tuple[str, str]:
    sem = (from_sem or "Odd").strip()
    if sem.lower().startswith("even"):
        return from_ay, "Odd"
    if "-" in from_ay:
        start_s, end_s = from_ay.split("-", 1)
        try:
            start = int(start_s)
            return f"{start + 1}-{start + 2}", "Even"
        except ValueError:
            pass
    return from_ay, "Even"


async def _rules(tenant_id) -> dict[str, str]:
    doc = await AcademicRegulation.find_one(
        Eq(AcademicRegulation.tenant_id, tenant_id),
        Eq(AcademicRegulation.scope_key, _SCOPE_KEY),
    )
    merged = deepcopy(_DEFAULT_RULES)
    if doc and doc.rules:
        for key, val in doc.rules.items():
            merged[key] = str(val)
    return merged


def _attendance_pct(rows: list[AttendanceRecord]) -> float | None:
    if not rows:
        return None
    present = sum(1 for row in rows if row.status in _PRESENT)
    return round((present / len(rows)) * 100, 1)


def _fee_overdue(demands: list[StudentFeeDemand], *, grace_days: int, today: date) -> bool:
    cutoff = today - timedelta(days=grace_days)
    for d in demands:
        if d.status == FeeDemandStatus.WAIVED:
            continue
        if d.status == FeeDemandStatus.OVERDUE:
            return True
        if d.status in (FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID) and d.due_date < cutoff:
            return True
    return False


async def _build_transition_options(tenant_id, from_ay: str, from_sem: str) -> list[StudentAdminDashboardFilterOption]:
    years = await AcademicYear.find(Eq(AcademicYear.tenant_id, tenant_id)).sort("-year_code").to_list()
    options: list[StudentAdminDashboardFilterOption] = []
    seen: set[str] = set()
    seeds = [(from_ay, from_sem)]
    for year in years[:4]:
        seeds.append((year.year_code, "Even"))
        seeds.append((year.year_code, "Odd"))
    for ay, sem in seeds:
        to_ay, to_sem = _infer_next_term(ay, sem)
        key = _transition_key(ay, sem, to_ay, to_sem)
        if key in seen:
            continue
        seen.add(key)
        options.append(
            StudentAdminDashboardFilterOption(
                value=key,
                label=_transition_label(ay, sem, to_ay, to_sem),
            )
        )
    fallback_to = _infer_next_term(from_ay, from_sem)
    return options or [
        StudentAdminDashboardFilterOption(
            value=_transition_key(from_ay, from_sem, fallback_to[0], fallback_to[1]),
            label=_transition_label(from_ay, from_sem, fallback_to[0], fallback_to[1]),
        )
    ]


async def _classify_students(
    tenant_id,
    *,
    ay_label: str | None,
    programme_code: str | None,
    rules: dict[str, str],
    today: date,
) -> tuple[dict[str, int], dict[str, int], list[dict]]:
    min_att = float(rules.get("min_attendance_pct", "75"))
    max_arrears = int(rules.get("max_arrears", "4"))
    grace_days = int(rules.get("fee_due_grace_days", "30"))

    policy = await AttendancePolicyReference.find_one(
        Eq(AttendancePolicyReference.tenant_id, tenant_id),
        Eq(AttendancePolicyReference.is_active, True),
    )
    if policy:
        min_att = float(policy.rules.min_percentage_required)

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog_by_code = {p.programme_code.upper(): p for p in programmes}

    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).to_list()
    records = [r for r in records if r.lifecycle_status in _ELIGIBLE_LIFECYCLE]
    if programme_code:
        records = [r for r in records if (r.programme_code or "").upper() == programme_code.upper()]

    user_ids = [r.user_id for r in records]
    if not user_ids:
        return (
            {"eligible": 0, "not_eligible": 0, "review": 0, "graduating": 0},
            {"attendance_below": 0, "arrears_above": 0, "fee_dues": 0},
            [],
        )

    attendance_rows = await AttendanceRecord.find(Eq(AttendanceRecord.tenant_id, tenant_id)).to_list()
    attendance_by_user: dict = defaultdict(list)
    for row in attendance_rows:
        attendance_by_user[row.student_user_id].append(row)

    arrears = await StudentArrearReference.find(
        Eq(StudentArrearReference.tenant_id, tenant_id),
        Eq(StudentArrearReference.backlog_status, BacklogStatus.PENDING),
    ).to_list()
    arrears_by_user: Counter = Counter(a.user_id for a in arrears)

    fee_demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    demands_by_user: dict = defaultdict(list)
    for d in fee_demands:
        demands_by_user[d.student_user_id].append(d)

    academic_records = await StudentAcademicRecord.find(Eq(StudentAcademicRecord.tenant_id, tenant_id)).to_list()
    standing_by_user: dict = {}
    progression_by_user: dict = {}
    for ar in academic_records:
        standing_by_user[ar.user_id] = ar.academic_standing
        progression_by_user[ar.user_id] = ar.progression_status

    buckets = {"eligible": 0, "not_eligible": 0, "review": 0, "graduating": 0}
    rule_counts = {"attendance_below": 0, "arrears_above": 0, "fee_dues": 0}
    eligible_users: list[dict] = []

    for record in records:
        prog = prog_by_code.get((record.programme_code or "").upper())
        max_sem = prog.duration_semesters if prog else 8
        study_year = _study_year(record.batch_label, ay_label)
        graduating = study_year is not None and study_year >= max_sem

        att = _attendance_pct(attendance_by_user.get(record.user_id, []))
        arrears_count = arrears_by_user.get(record.user_id, 0)
        fee_bad = _fee_overdue(demands_by_user.get(record.user_id, []), grace_days=grace_days, today=today)
        standing = standing_by_user.get(record.user_id, AcademicStanding.UNKNOWN)
        progression = progression_by_user.get(record.user_id, ProgressionStatus.PENDING)

        if att is not None and att < min_att:
            rule_counts["attendance_below"] += 1
        if arrears_count > max_arrears:
            rule_counts["arrears_above"] += 1
        if fee_bad:
            rule_counts["fee_dues"] += 1

        if graduating:
            buckets["graduating"] += 1
            continue

        fails_hard = (att is not None and att < min_att) or arrears_count > max_arrears or fee_bad
        needs_review = (
            standing in (AcademicStanding.PROBATION, AcademicStanding.SUSPENDED)
            or progression == ProgressionStatus.PENDING
            or (att is not None and min_att - 5 <= att < min_att)
            or arrears_count == max_arrears
        )

        if fails_hard:
            buckets["not_eligible"] += 1
        elif needs_review:
            buckets["review"] += 1
        else:
            buckets["eligible"] += 1
            eligible_users.append({"record": record, "user_id": record.user_id})

    return buckets, rule_counts, eligible_users


async def get_student_promotion_management_page(
    scope: AccessScope,
    *,
    transition_key: str | None = None,
    programme_code: str | None = None,
    preview: bool = False,
) -> StudentPromotionManagementPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.date()

    from_ay, from_sem = await _reader.current_academic_term(tenant_id)
    from_ay = from_ay or ""
    from_sem = from_sem or "Odd"
    to_ay, to_sem = _infer_next_term(from_ay, from_sem)
    default_transition = _transition_key(from_ay, from_sem, to_ay, to_sem)
    sel_from_ay, sel_from_sem, sel_to_ay, sel_to_sem = _parse_transition_key(
        transition_key,
        (from_ay, from_sem, to_ay, to_sem),
    )

    rules = await _rules(tenant_id)
    buckets, rule_counts, _ = await _classify_students(
        tenant_id,
        ay_label=sel_from_ay or from_ay,
        programme_code=programme_code,
        rules=rules,
        today=today,
    )

    regulation_code = rules.get("regulation_code", "R2022")
    catalog = await AcademicRegulationCatalog.find_one(
        Eq(AcademicRegulationCatalog.tenant_id, tenant_id),
        Eq(AcademicRegulationCatalog.regulation_code, regulation_code),
    )
    regulation_label = catalog.display_label if catalog else f"academic regulation {regulation_code}"

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    programme_options = [StudentAdminDashboardFilterOption(value="", label="All programmes")]
    for prog in sorted(programmes, key=lambda p: p.programme_code):
        programme_options.append(
            StudentAdminDashboardFilterOption(value=prog.programme_code.upper(), label=prog.name or prog.programme_code)
        )

    transition_options = await _build_transition_options(tenant_id, from_ay, from_sem)
    selected_transition = _transition_key(sel_from_ay, sel_from_sem, sel_to_ay, sel_to_sem)

    min_att = rules.get("min_attendance_pct", "75")
    max_arrears = rules.get("max_arrears", "4")
    grace = rules.get("fee_due_grace_days", "30")

    rule_rows = [
        StudentPromotionRuleRow(
            rule_key="attendance",
            rule_label="Attendance",
            requirement_label=f"{min_att}% or more",
            affected_label=f"{rule_counts['attendance_below']:,} below",
        ),
        StudentPromotionRuleRow(
            rule_key="backlogs",
            rule_label="Backlogs",
            requirement_label=f"No more than {max_arrears} arrears",
            affected_label=f"{rule_counts['arrears_above']:,} above",
        ),
        StudentPromotionRuleRow(
            rule_key="fees",
            rule_label="Fees",
            requirement_label=f"No dues beyond {grace} days",
            affected_label=f"{rule_counts['fee_dues']:,} with dues",
        ),
    ]

    kpis = [
        UserDashboardKpi(
            key="eligible",
            label="Eligible",
            value=f"{buckets['eligible']:,}",
            hint_line="Meet criteria",
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="not_eligible",
            label="Not eligible",
            value=f"{buckets['not_eligible']:,}",
            hint_line="Backlogs or attendance",
            hint_tone="error",
        ),
        UserDashboardKpi(
            key="review",
            label="Review",
            value=f"{buckets['review']:,}",
            hint_line="Manual decision",
            hint_tone="warning",
        ),
        UserDashboardKpi(
            key="graduating",
            label="Graduating",
            value=f"{buckets['graduating']:,}",
            hint_line="Final semester",
            hint_tone="info",
        ),
    ]

    preview_note = None
    if preview:
        preview_note = f"Preview: {buckets['eligible']:,} students would be promoted to {sel_to_sem} {_ay_display(sel_to_ay)}."

    return StudentPromotionManagementPageRead(
        page_title="Student Promotion Management",
        page_subtitle="Promote students to the next semester",
        preview_label="Preview",
        promote_eligible_label="Promote eligible",
        transition_filter_label="Promotion period",
        programme_filter_label="Programme",
        scope_indicator_label="College scope",
        updated_at_label=_fmt_time_label(now),
        transition_options=transition_options,
        programme_options=programme_options,
        selected_transition_key=selected_transition,
        selected_programme_code=programme_code or "",
        kpis=kpis,
        promotion_rules_section_title="Promotion rules",
        promotion_rules_footer_label=f"Rules from {regulation_label}",
        promotion_rules_table_headers=["Rule", "Requirement", "Students affected"],
        promotion_rules_rows=rule_rows,
        preview_note=preview_note,
        footer_disclaimer="Live institutional data · Student promotion and academic records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def preview_student_promotion(
    scope: AccessScope,
    *,
    transition_key: str | None = None,
    programme_code: str | None = None,
) -> StudentPromotionManagementPageRead:
    return await get_student_promotion_management_page(
        scope,
        transition_key=transition_key,
        programme_code=programme_code,
        preview=True,
    )


async def promote_eligible_students(
    scope: AccessScope,
    payload: StudentPromotionPromotePayload,
) -> StudentPromotionManagementPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    from_ay, from_sem = await _reader.current_academic_term(tenant_id)
    from_ay = from_ay or ""
    from_sem = from_sem or "Odd"
    to_ay, to_sem = _infer_next_term(from_ay, from_sem)
    sel_from_ay, sel_from_sem, sel_to_ay, sel_to_sem = _parse_transition_key(
        payload.transition_key,
        (from_ay, from_sem, to_ay, to_sem),
    )

    rules = await _rules(tenant_id)
    _, _, eligible_users = await _classify_students(
        tenant_id,
        ay_label=sel_from_ay,
        programme_code=payload.programme_code,
        rules=rules,
        today=now.date(),
    )

    for item in eligible_users:
        record: StudentRecord = item["record"]
        promotion = StudentPromotionRecord(
            tenant_id=tenant_id,
            user_id=record.user_id,
            from_academic_year=sel_from_ay,
            from_semester=sel_from_sem,
            to_academic_year=sel_to_ay,
            to_semester=sel_to_sem,
            decision="promoted",
            actor_id=scope.user_id,
        )
        await promotion.insert()

        academic = await StudentAcademicRecord.find_one(
            Eq(StudentAcademicRecord.tenant_id, tenant_id),
            Eq(StudentAcademicRecord.user_id, record.user_id),
            Eq(StudentAcademicRecord.academic_year_label, sel_from_ay),
            Eq(StudentAcademicRecord.semester_label, sel_from_sem),
        )
        if academic:
            academic.academic_year_label = sel_to_ay
            academic.semester_label = sel_to_sem
            academic.progression_status = ProgressionStatus.PROMOTED
            academic.updated_at = now
            await academic.save()
        else:
            doc = StudentAcademicRecord(
                tenant_id=tenant_id,
                user_id=record.user_id,
                academic_year_label=sel_to_ay,
                semester_label=sel_to_sem,
                progression_status=ProgressionStatus.PROMOTED,
                effective_from=now.date(),
            )
            await doc.insert()

    return await get_student_promotion_management_page(
        scope,
        transition_key=payload.transition_key,
        programme_code=payload.programme_code,
    )