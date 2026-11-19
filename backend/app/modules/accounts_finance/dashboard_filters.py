"""Finance dashboard filter context."""

from dataclasses import dataclass
from datetime import date, datetime, time, timezone

from beanie import PydanticObjectId

from app.common.ids import to_object_id


@dataclass(frozen=True)
class FinanceDashboardContext:
    tenant_id: PydanticObjectId
    academic_year_label: str | None
    semester_label: str | None
    programme_code: str | None
    department_id: PydanticObjectId | None
    campus_id: PydanticObjectId | None
    date_from: datetime | None
    date_to: datetime | None
    payment_status: str | None
    payment_method: str | None


def build_dashboard_context(
    tenant_id: PydanticObjectId,
    *,
    academic_year_label: str | None,
    semester_label: str | None,
    programme_code: str | None,
    department_id: str | None,
    campus_id: str | None,
    date_from: date | None,
    date_to: date | None,
    payment_status: str | None,
    payment_method: str | None,
) -> FinanceDashboardContext:
    dept = to_object_id(department_id, "department_id") if department_id else None
    campus = to_object_id(campus_id, "campus_id") if campus_id else None
    dt_from = datetime.combine(date_from, time.min, tzinfo=timezone.utc) if date_from else None
    dt_to = datetime.combine(date_to, time.max, tzinfo=timezone.utc) if date_to else None
    return FinanceDashboardContext(
        tenant_id=tenant_id,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        programme_code=programme_code.upper() if programme_code else None,
        department_id=dept,
        campus_id=campus,
        date_from=dt_from,
        date_to=dt_to,
        payment_status=payment_status,
        payment_method=payment_method,
    )