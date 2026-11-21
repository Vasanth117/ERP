"""Campus address, contacts and emergency information page."""

from __future__ import annotations

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.modules.audit.service import record_audit
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.campus_ext_models import (
    InstitutionCampusEmergencyContact,
    InstitutionCampusOfficialContact,
)
from app.modules.college_admin.institution_service import list_campuses
from app.modules.college_admin.models import InstitutionCampus
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CampusContactPageRead,
    CampusContactPageSave,
    CampusEmergencyContactRow,
    CampusOfficialContactRow,
    CampusTabLink,
    InstitutionFieldMeta,
    InstitutionFieldOption,
    InstitutionUsageContext,
)


_ADDRESS_FIELD_META = [
    InstitutionFieldMeta(key="line1", label="Address line 1", required=True, field_type="text"),
    InstitutionFieldMeta(key="line2", label="Address line 2", required=False, field_type="text"),
    InstitutionFieldMeta(key="city", label="City", required=True, field_type="text"),
    InstitutionFieldMeta(key="district", label="District", required=True, field_type="select"),
    InstitutionFieldMeta(key="state", label="State", required=True, field_type="select"),
    InstitutionFieldMeta(key="postal_code", label="PIN code", required=True, field_type="text"),
    InstitutionFieldMeta(key="latitude", label="Latitude", required=False, field_type="text"),
    InstitutionFieldMeta(key="longitude", label="Longitude", required=False, field_type="text"),
]

_CAMPUS_USAGE_CONTEXTS = [
    InstitutionUsageContext(
        title="Admission portal",
        description="Address + admissions contact",
    ),
    InstitutionUsageContext(
        title="Fee receipts",
        description="Full postal address",
    ),
    InstitutionUsageContext(
        title="Student ID cards",
        description="City and phone",
    ),
]


async def _resolve_campus(scope: AccessScope, campus_id: PydanticObjectId) -> InstitutionCampus:
    tenant_id = require_college_tenant_scope(scope)
    campus = await InstitutionCampus.find_one(
        Eq(InstitutionCampus.tenant_id, tenant_id),
        Eq(InstitutionCampus.id, campus_id),
    )
    if campus is None:
        raise AppError(code="NOT_FOUND", message="Campus not found", status_code=404)
    return campus


def _distinct_options(values: list[str]) -> list[InstitutionFieldOption]:
    seen: set[str] = set()
    options: list[InstitutionFieldOption] = []
    for value in values:
        key = value.strip()
        if not key or key.lower() in seen:
            continue
        seen.add(key.lower())
        options.append(InstitutionFieldOption(value=key, label=key))
    return options


async def get_campus_contact_page(scope: AccessScope, campus_id: PydanticObjectId) -> CampusContactPageRead:
    authorize(scope, Permission.INSTITUTION_PROFILE_READ)
    tenant_id = require_college_tenant_scope(scope)
    campus = await _resolve_campus(scope, campus_id)
    campus_key = str(campus.id)

    all_campuses = await list_campuses(scope, active_only=False)
    campus_tabs = [
        CampusTabLink(
            campus_id=row.campus_id,
            name=row.name,
            href=f"/college-admin/institution/campuses/{row.campus_id}/contact",
            is_active=row.campus_id == campus_key,
        )
        for row in all_campuses
    ]

    campus_docs = await InstitutionCampus.find(Eq(InstitutionCampus.tenant_id, tenant_id)).to_list()
    states = _distinct_options([doc.address.state for doc in campus_docs if doc.address.state])
    districts = _distinct_options([doc.address.district or "" for doc in campus_docs if doc.address.district])
    if campus.address.state and not any(o.value == campus.address.state for o in states):
        states.insert(0, InstitutionFieldOption(value=campus.address.state, label=campus.address.state))
    if campus.address.district and not any(o.value == campus.address.district for o in districts):
        districts.insert(0, InstitutionFieldOption(value=campus.address.district, label=campus.address.district))
    if not states:
        states = [InstitutionFieldOption(value="", label="Select state")]
    if not districts:
        districts = [InstitutionFieldOption(value="", label="Select district")]

    official = await InstitutionCampusOfficialContact.find(
        Eq(InstitutionCampusOfficialContact.tenant_id, tenant_id),
        Eq(InstitutionCampusOfficialContact.campus_id, campus.id),
    ).sort("+sort_order").to_list()
    emergency = await InstitutionCampusEmergencyContact.find(
        Eq(InstitutionCampusEmergencyContact.tenant_id, tenant_id),
        Eq(InstitutionCampusEmergencyContact.campus_id, campus.id),
    ).sort("+sort_order").to_list()

    official_rows = [
        CampusOfficialContactRow(
            contact_id=row.contact_id,
            role_label=row.role_label,
            name=row.name,
            phone=row.phone,
            email=row.email,
        )
        for row in official
    ]
    emergency_rows = [
        CampusEmergencyContactRow(contact_id=row.contact_id, label=row.label, phone=row.phone)
        for row in emergency
    ]

    count_label = f"{len(official_rows)} contact{'s' if len(official_rows) != 1 else ''}"

    return CampusContactPageRead(
        page_title="Campus address & contact",
        campus_tabs=campus_tabs,
        address=campus.address,
        address_field_meta=_ADDRESS_FIELD_META,
        state_options=states,
        district_options=districts,
        official_contacts=official_rows,
        contact_count_label=count_label,
        add_contact_enabled=True,
        usage_contexts=_CAMPUS_USAGE_CONTEXTS,
        emergency_contacts=emergency_rows,
        footer_note="Changes are saved to the audit log with your name and time.",
        cancel_href=f"/college-admin/institution/campuses/{campus_key}",
        generated_at=utcnow(),
    )


async def save_campus_contact_page(
    scope: AccessScope,
    campus_id: PydanticObjectId,
    payload: CampusContactPageSave,
) -> CampusContactPageRead:
    authorize(scope, Permission.INSTITUTION_CAMPUS_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    campus = await _resolve_campus(scope, campus_id)

    campus.address = payload.address
    campus.updated_at = utcnow()
    campus.updated_by = scope.user_id
    await campus.save()

    await InstitutionCampusOfficialContact.find(
        Eq(InstitutionCampusOfficialContact.tenant_id, tenant_id),
        Eq(InstitutionCampusOfficialContact.campus_id, campus.id),
    ).delete()
    for index, item in enumerate(payload.official_contacts):
        contact_id = item.contact_id or f"ct-{uuid4().hex[:10]}"
        await InstitutionCampusOfficialContact(
            tenant_id=tenant_id,
            campus_id=campus.id,
            contact_id=contact_id,
            role_label=item.role_label,
            name=item.name,
            phone=item.phone,
            email=str(item.email).lower() if item.email else None,
            sort_order=index,
        ).insert()

    await InstitutionCampusEmergencyContact.find(
        Eq(InstitutionCampusEmergencyContact.tenant_id, tenant_id),
        Eq(InstitutionCampusEmergencyContact.campus_id, campus.id),
    ).delete()
    for index, item in enumerate(payload.emergency_contacts):
        contact_id = item.contact_id or f"em-{uuid4().hex[:10]}"
        await InstitutionCampusEmergencyContact(
            tenant_id=tenant_id,
            campus_id=campus.id,
            contact_id=contact_id,
            label=item.label,
            phone=item.phone,
            sort_order=index,
        ).insert()

    await record_audit(
        actor_id=scope.user_id,
        action="institution.campus.contact.updated",
        resource_type="institution_campus",
        resource_id=str(campus.id),
        tenant_id=tenant_id,
        metadata={"official_contacts": len(payload.official_contacts)},
    )

    return await get_campus_contact_page(scope, campus_id)