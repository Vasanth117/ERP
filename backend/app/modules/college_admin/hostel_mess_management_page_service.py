"""Hostel mess management (CA 13.09)."""

from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.models import InstitutionSettings
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HostelMessFeedbackDimension,
    HostelMessManagementPageRead,
    HostelMessMenuRow,
    UserDashboardKpi,
)
from app.modules.hostel.mess_models import (
    HostelMealAttendance,
    HostelMealCategory,
    HostelMenu,
    HostelMessEnrollment,
    MessEnrollmentStatus,
    HostelMessPlan,
)

_IST = ZoneInfo("Asia/Kolkata")
_DEFAULT_FEEDBACK: list[tuple[str, str]] = [
    ("taste", "Taste"),
    ("hygiene", "Hygiene"),
    ("quantity", "Quantity"),
]


def _menu_text(items: list) -> str:
    parts: list[str] = []
    for it in items:
        if isinstance(it, dict):
            label = it.get("name") or it.get("label") or it.get("title")
            if label:
                parts.append(str(label))
        elif it:
            parts.append(str(it))
    return ", ".join(parts) if parts else "—"


def _plan_kind(plan: HostelMessPlan | None) -> str | None:
    if plan is None:
        return None
    blob = f"{plan.title or ''} {plan.description or ''} {' '.join(plan.included_meals)}".lower()
    if "non" in blob and "veg" in blob:
        return "non_veg"
    if "veg" in blob:
        return "veg"
    return None


def _feedback_tone(key: str) -> str:
    if key == "hygiene":
        return "success"
    if key == "quantity":
        return "warning"
    return "info"


async def _load_mess_settings(tenant_id: PydanticObjectId) -> dict:
    settings = await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))
    if not settings:
        return {}
    hostel = settings.settings.get("hostel") or {}
    return hostel.get("mess") or {}


async def get_hostel_mess_management_page(scope: AccessScope) -> HostelMessManagementPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()

    attendances = await HostelMealAttendance.find(
        Eq(HostelMealAttendance.tenant_id, tenant_id),
        Eq(HostelMealAttendance.service_date, today),
        Eq(HostelMealAttendance.attended, True),
    ).to_list()
    meals_today = len(attendances)

    enrollments = await HostelMessEnrollment.find(
        Eq(HostelMessEnrollment.tenant_id, tenant_id),
        Eq(HostelMessEnrollment.status, MessEnrollmentStatus.ACTIVE),
    ).to_list()
    plans = await HostelMessPlan.find(Eq(HostelMessPlan.tenant_id, tenant_id)).to_list()
    plan_by_code = {p.plan_code: p for p in plans}
    veg_count = 0
    nonveg_count = 0
    for enr in enrollments:
        kind = _plan_kind(plan_by_code.get(enr.plan_code))
        if kind == "veg":
            veg_count += 1
        elif kind == "non_veg":
            nonveg_count += 1

    mess_cfg = await _load_mess_settings(tenant_id)
    feedback_cfg = mess_cfg.get("feedback") or mess_cfg.get("feedback_scores") or {}

    categories = await HostelMealCategory.find(Eq(HostelMealCategory.tenant_id, tenant_id), Eq(HostelMealCategory.active, True)).to_list()
    category_label = {c.category_code.upper(): c.label for c in categories}

    menus = await HostelMenu.find(
        Eq(HostelMenu.tenant_id, tenant_id),
        Eq(HostelMenu.service_date, today),
    ).to_list()
    published_menus = [m for m in menus if m.published] or menus

    served_by_meal: dict[str, int] = {}
    for row in attendances:
        key = (row.meal_category_code or "unknown").upper()
        served_by_meal[key] = served_by_meal.get(key, 0) + 1

    menu_rows: list[HostelMessMenuRow] = []
    seen_meals: set[str] = set()
    for menu in published_menus:
        code = (menu.meal_category_code or menu.menu_id).upper()
        label = category_label.get(code, code.replace("_", " ").title())
        served = served_by_meal.get(code, 0)
        menu_rows.append(
            HostelMessMenuRow(
                meal_key=menu.menu_id,
                meal_label=label,
                menu_label=_menu_text(menu.items),
                served_label=f"{served:,}",
            )
        )
        seen_meals.add(code)

    for category in categories:
        code = category.category_code.upper()
        if code in seen_meals:
            continue
        menu_rows.append(
            HostelMessMenuRow(
                meal_key=code,
                meal_label=category.label,
                menu_label="—",
                served_label=f"{served_by_meal.get(code, 0):,}",
            )
        )

    menu_rows.sort(key=lambda r: r.meal_label)

    feedback_dimensions: list[HostelMessFeedbackDimension] = []
    scores: list[float] = []
    for key, label in _DEFAULT_FEEDBACK:
        raw = feedback_cfg.get(key)
        if raw is None and isinstance(feedback_cfg.get("dimensions"), dict):
            raw = feedback_cfg["dimensions"].get(key)
        try:
            score = float(raw) if raw is not None else 0.0
        except (TypeError, ValueError):
            score = 0.0
        if score > 0:
            scores.append(score)
        max_score = 5.0
        progress = int(round((score / max_score) * 100)) if max_score else 0
        feedback_dimensions.append(
            HostelMessFeedbackDimension(
                key=key,
                label=label,
                score_label=f"{score:.1f}",
                progress_percent=min(100, max(0, progress)),
                tone=_feedback_tone(key),
            )
        )

    overall = sum(scores) / len(scores) if scores else 0.0
    overall_label = f"{overall:.1f} / 5" if scores else "— / 5"

    kpis = [
        UserDashboardKpi(
            key="meals_served_today",
            label="Meals served today",
            value=f"{meals_today:,}",
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="veg_plan",
            label="Veg plan",
            value=f"{veg_count:,}",
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="non_veg_plan",
            label="Non-veg plan",
            value=f"{nonveg_count:,}",
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="feedback_score",
            label="Feedback score",
            value=overall_label,
            hint_line="",
            hint_tone="info" if scores else "muted",
        ),
    ]

    return HostelMessManagementPageRead(
        page_title="Mess Management",
        page_subtitle="Menu, meal plans and attendance",
        edit_menu_label="Edit menu",
        edit_menu_href="/college-admin/hostel/mess-management?action=edit-menu",
        kpis=kpis,
        menu_section_title="Today's menu",
        menu_table_headers=["Meal", "Menu", "Served"],
        menu_rows=menu_rows,
        empty_menu_message="No menu published for today.",
        feedback_section_title="Feedback",
        feedback_dimensions=feedback_dimensions,
        generated_at=now,
    )