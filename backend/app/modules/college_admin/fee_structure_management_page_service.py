"""Fee structure management list page (CA 10.02)."""

from __future__ import annotations

import math
import re

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.finance_admin_models import InstitutionFeeStructure
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    FeeStructureManagementPageRead,
    FeeStructureManagementTableRow,
    PoliciesPagination,
)

_PAGE_SIZE = 10


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _format_inr(amount: float) -> str:
    rupees = int(round(amount))
    s = str(rupees)
    if len(s) <= 3:
        return f"₹{s}"
    last3 = s[-3:]
    rest = s[:-3]
    groups: list[str] = []
    while rest:
        take = 2 if len(rest) > 2 else len(rest)
        groups.insert(0, rest[-take:])
        rest = rest[:-take]
    return f"₹{','.join(groups + [last3])}"


def _year_display(label: str) -> str:
    if not label:
        return "—"
    match = re.match(r"^(\d{4})-(\d{4})$", label.strip())
    if match:
        return f"{match.group(1)}-{match.group(2)[-2:]}"
    match = re.match(r"^(\d{4})-(\d{2})$", label.strip())
    if match:
        return label
    return label


def _semester_display(semester: str) -> str:
    if not semester:
        return ""
    s = semester.strip()
    if re.match(r"^\d+$", s):
        return f"Sem {s}"
    if s.lower().startswith("sem"):
        return s.title() if s.islower() else s
    return s


def _structure_label(doc: InstitutionFeeStructure) -> str:
    if " - " in doc.structure_id:
        return doc.structure_id
    sem = _semester_display(doc.semester_label)
    code = (doc.programme_code or "FEE").split("-")[0].upper()
    return f"{code} - General - {sem}" if sem else doc.structure_id


def _programme_label(code: str, programmes: dict[str, AcademicProgramme]) -> str:
    prog = programmes.get(code.upper())
    if prog and prog.name:
        return prog.name
    if code:
        return code.replace("-", " ").replace("_", " ")
    return "—"


def _status(doc: InstitutionFeeStructure) -> tuple[str, str]:
    if doc.published:
        return "Active", "success"
    return "Pending approval", "warning"


async def get_fee_structure_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
) -> FeeStructureManagementPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    structures = await InstitutionFeeStructure.find(Eq(InstitutionFeeStructure.tenant_id, tenant_id)).sort(
        "-updated_at"
    ).to_list()

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog_by_code = {p.programme_code.upper(): p for p in programmes}

    total = len(structures)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_rows = structures[start : start + _PAGE_SIZE]

    rows: list[FeeStructureManagementTableRow] = []
    for doc in page_rows:
        status_label, status_tone = _status(doc)
        rows.append(
            FeeStructureManagementTableRow(
                structure_id=doc.structure_id,
                structure_label=_structure_label(doc),
                year_label=_year_display(doc.academic_year_label),
                programme_label=_programme_label(doc.programme_code, prog_by_code),
                total_label=_format_inr(doc.total_amount),
                status_label=status_label,
                status_tone=status_tone,
                detail_href="/college-admin/finance/fee-structure-management",
            )
        )

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    return FeeStructureManagementPageRead(
        page_title="Fee Structure Management",
        page_subtitle="Approved fee structures by programme and semester",
        create_fee_structure_label="Create fee structure",
        create_fee_structure_href="/college-admin/finance/fee-structure-management?create=1",
        structures_section_title="Fee structures",
        structures_count_label=f"{total} structure{'s' if total != 1 else ''}" if total else "0 structures",
        table_headers=["Fee structure", "Year", "Programme", "Total", "Status"],
        structures=rows,
        showing_label=f"Showing {showing_from}–{showing_to} of {total}" if total else "Showing 0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        info_notice_title="Issued invoices are not changed",
        info_notice_body="Revisions apply only from their effective date. Previous versions are kept.",
        generated_at=now,
    )