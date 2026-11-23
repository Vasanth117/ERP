"""Create / edit department page (CA 04 — organization)."""

from __future__ import annotations

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.roles import Role
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.identity_models import (
    DepartmentKind,
    DepartmentStatus,
    InstitutionDepartment,
    InstitutionOrganizationUnit,
    OrganizationUnitType,
)
from app.modules.college_admin.identity_schemas import InstitutionDepartmentCreate, InstitutionDepartmentUpdate
from app.modules.college_admin.institution_service import list_campuses
from app.modules.college_admin.operations_ext_models import InstitutionFacility
from app.modules.college_admin.organization_service import (
    create_institution_department,
    update_institution_department,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    CreateEditDepartmentChecklistStep,
    CreateEditDepartmentFormValues,
    CreateEditDepartmentPageRead,
    CreateEditDepartmentSavePayload,
    CreateEditDepartmentTemplateOption,
    InstitutionFieldMeta,
    InstitutionFieldOption,
)

_DETAILS_META = [
    InstitutionFieldMeta(key="name", label="Department name", required=True),
    InstitutionFieldMeta(key="department_code", label="Department code", required=True),
    InstitutionFieldMeta(key="department_kind", label="Department type", required=True, field_type="radio"),
    InstitutionFieldMeta(key="organization_unit_id", label="School / faculty", required=True, field_type="select"),
    InstitutionFieldMeta(key="campus_id", label="Campus", required=True, field_type="select"),
    InstitutionFieldMeta(key="establishment_year", label="Year of establishment", required=True, field_type="number"),
    InstitutionFieldMeta(key="building_floor_label", label="Building & floor", field_type="select"),
    InstitutionFieldMeta(key="contact_email", label="Department email", field_type="email"),
    InstitutionFieldMeta(key="vision_mission", label="Vision & mission", field_type="textarea"),
]

_SETUP_META = [
    InstitutionFieldMeta(key="head_user_id", label="Head of department", field_type="select"),
    InstitutionFieldMeta(key="approved_intake_ug", label="Approved intake (UG)", field_type="number"),
    InstitutionFieldMeta(key="aicte_approval_reference", label="AICTE approval reference"),
    InstitutionFieldMeta(key="cost_centre_code", label="Cost centre (finance)", field_type="select"),
]

_KIND_OPTIONS = [
    InstitutionFieldOption(value=DepartmentKind.ACADEMIC.value, label="Academic"),
    InstitutionFieldOption(value=DepartmentKind.ADMINISTRATIVE.value, label="Administrative"),
]


def _default_form() -> CreateEditDepartmentFormValues:
    return CreateEditDepartmentFormValues(
        name="",
        department_code="",
        department_kind=DepartmentKind.ACADEMIC.value,
        organization_unit_id="",
        campus_id="",
        establishment_year=None,
        building_floor_label="",
        contact_email="",
        vision_mission="",
        head_user_id="",
        approved_intake_ug=None,
        aicte_approval_reference="",
        cost_centre_code="",
        settings_template_department_id="",
    )


def _form_from_doc(doc: InstitutionDepartment) -> CreateEditDepartmentFormValues:
    campus_id = str(doc.campus_ids[0]) if doc.campus_ids else ""
    return CreateEditDepartmentFormValues(
        name=doc.name,
        department_code=doc.department_code,
        department_kind=doc.department_kind.value,
        organization_unit_id=str(doc.organization_unit_id) if doc.organization_unit_id else "",
        campus_id=campus_id,
        establishment_year=doc.establishment_year,
        building_floor_label=doc.building_floor_label or "",
        contact_email=doc.contact_email or "",
        vision_mission=doc.description or "",
        head_user_id=str(doc.head_user_id) if doc.head_user_id else "",
        approved_intake_ug=doc.approved_intake_ug,
        aicte_approval_reference=doc.aicte_approval_reference or "",
        cost_centre_code=doc.cost_centre_code or "",
        settings_template_department_id=(
            str(doc.settings_template_department_id) if doc.settings_template_department_id else ""
        ),
    )


async def _load_options(tenant_id: PydanticObjectId, scope: AccessScope) -> dict:
    org_units = await InstitutionOrganizationUnit.find(
        Eq(InstitutionOrganizationUnit.tenant_id, tenant_id),
    ).sort("+name").to_list()
    schools = [
        u
        for u in org_units
        if u.unit_type in (OrganizationUnitType.SCHOOL, OrganizationUnitType.FACULTY)
    ]
    school_options = [InstitutionFieldOption(value="", label="Select school / faculty")]
    for unit in schools:
        school_options.append(InstitutionFieldOption(value=str(unit.id), label=unit.name))

    campuses = await list_campuses(scope, active_only=True)
    campus_options = [InstitutionFieldOption(value="", label="Select campus")]
    for campus in campuses:
        campus_options.append(InstitutionFieldOption(value=campus.campus_id, label=campus.name))

    facilities = await InstitutionFacility.find(
        Eq(InstitutionFacility.tenant_id, tenant_id),
        Eq(InstitutionFacility.active, True),
    ).to_list()
    building_options = [InstitutionFieldOption(value="", label="Select building & floor")]
    for facility in sorted(facilities, key=lambda row: row.name):
        if facility.facility_type not in {"building", "block", "classroom"}:
            continue
        building_options.append(InstitutionFieldOption(value=facility.name, label=facility.name))

    departments = await InstitutionDepartment.find(Eq(InstitutionDepartment.tenant_id, tenant_id)).to_list()
    cost_codes = sorted({d.cost_centre_code for d in departments if d.cost_centre_code})
    cost_options = [InstitutionFieldOption(value="", label="Select or enter cost centre")]
    for code in cost_codes:
        cost_options.append(InstitutionFieldOption(value=code, label=code))

    faculty_users = await User.find(
        Eq(User.tenant_id, tenant_id),
        In(User.role, [Role.FACULTY, Role.DEPARTMENT_ADMIN, Role.COLLEGE_ADMIN]),
    ).sort("+full_name").to_list()
    head_options = [InstitutionFieldOption(value="", label="Assign later")]
    for user in faculty_users:
        head_options.append(InstitutionFieldOption(value=str(user.id), label=user.full_name))

    templates: list[CreateEditDepartmentTemplateOption] = [
        CreateEditDepartmentTemplateOption(
            template_key="blank",
            title="Start blank",
            subtitle="Use college defaults",
            action_label="Use →",
            department_id="",
        )
    ]
    for dept in sorted(departments, key=lambda d: d.name):
        if dept.status == DepartmentStatus.ARCHIVED:
            continue
        if dept.department_kind != DepartmentKind.ACADEMIC:
            continue
        templates.append(
            CreateEditDepartmentTemplateOption(
                template_key=f"dept_{dept.id}",
                title=dept.name,
                subtitle="Rules, grading, attendance",
                action_label="Use →",
                department_id=str(dept.id),
            )
        )

    return {
        "school_options": school_options,
        "campus_options": campus_options,
        "building_options": building_options,
        "cost_centre_options": cost_options,
        "head_options": head_options,
        "template_options": templates,
    }


def _checklist(*, is_create: bool, has_head: bool) -> list[CreateEditDepartmentChecklistStep]:
    steps = [
        CreateEditDepartmentChecklistStep(
            key="create",
            label="Department details",
            hint="This step" if is_create else "Completed",
            state="current" if is_create else "complete",
        ),
        CreateEditDepartmentChecklistStep(
            key="assign_head",
            label="Assign head of department",
            hint="Required before programmes",
            state="complete" if has_head else "pending",
        ),
        CreateEditDepartmentChecklistStep(
            key="map_programmes",
            label="Map programmes & courses",
            hint="Academic configuration",
            state="pending",
        ),
        CreateEditDepartmentChecklistStep(
            key="allocate_faculty",
            label="Allocate faculty",
            hint="At least 6 faculty",
            state="pending",
        ),
    ]
    return steps


async def get_create_edit_department_page(
    scope: AccessScope,
    department_id: PydanticObjectId | None,
) -> CreateEditDepartmentPageRead:
    authorize(scope, Permission.INSTITUTION_ORG_READ)
    tenant_id = require_college_tenant_scope(scope)
    is_create = department_id is None

    opts = await _load_options(tenant_id, scope)
    form = _default_form()

    if department_id is not None:
        doc = await InstitutionDepartment.get(department_id)
        if doc is None or doc.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Department not found", status_code=404)
        form = _form_from_doc(doc)
        has_head = doc.head_user_id is not None
        page_title = "Edit department"
        save_label = "Save changes"
    else:
        has_head = False
        page_title = "Create Department"
        save_label = "Create department"

    return CreateEditDepartmentPageRead(
        page_title=page_title,
        page_subtitle="Add a new academic or administrative department",
        cancel_href="/college-admin/organization/all-departments",
        cancel_label="Cancel",
        save_label=save_label,
        save_draft_label="Save draft",
        create_label="Create department",
        details_section_title="Department details",
        setup_section_title="Initial setup",
        copy_settings_title="Copy settings from",
        checklist_title="Setup checklist",
        details_field_meta=_DETAILS_META,
        setup_field_meta=_SETUP_META,
        department_kind_options=_KIND_OPTIONS,
        school_options=opts["school_options"],
        campus_options=opts["campus_options"],
        building_options=opts["building_options"],
        cost_centre_options=opts["cost_centre_options"],
        head_options=opts["head_options"],
        template_options=opts["template_options"],
        checklist_steps=_checklist(is_create=is_create, has_head=has_head),
        form=form,
        department_id=str(department_id) if department_id else None,
        is_create=is_create,
        can_save=True,
        footer_note="New departments stay in Draft until a head is assigned and the Principal approves.",
        footer_disclaimer="Live institutional data · Department records · All times IST",
        generated_at=utcnow(),
    )


def _label_for_field_key(field_key: str) -> str:
    for row in _DETAILS_META:
        if row.key == field_key:
            return row.label
    return field_key.replace("_", " ").title()


def _validation_detail(
    field_key: str,
    *,
    school_selectable: int,
    campus_selectable: int,
) -> dict[str, str | None]:
    label = _label_for_field_key(field_key)
    if field_key == "organization_unit_id":
        if school_selectable <= 0:
            return {
                "field_key": field_key,
                "label": label,
                "message": "No schools or faculties are set up yet. Add one before creating a department.",
                "action_type": "navigate",
                "action_label": "Open organization hierarchy",
                "action_href": "/college-admin/organization/organizational-hierarchy",
            }
        return {
            "field_key": field_key,
            "label": label,
            "message": "Select which school or faculty this department belongs to.",
            "action_type": "scroll",
            "action_label": "Go to School / faculty",
            "action_href": None,
        }
    if field_key == "campus_id":
        if campus_selectable <= 0:
            return {
                "field_key": field_key,
                "label": label,
                "message": "No campuses are configured for this institution.",
                "action_type": "navigate",
                "action_label": "Manage campuses",
                "action_href": "/college-admin/institution/campuses",
            }
        return {
            "field_key": field_key,
            "label": label,
            "message": "Select the campus where this department is located.",
            "action_type": "scroll",
            "action_label": "Go to Campus",
            "action_href": None,
        }
    messages: dict[str, tuple[str, str]] = {
        "name": ("Enter the full display name of the department.", "Go to Department name"),
        "department_code": ("Enter a unique department code (e.g. CSE, MBA).", "Go to Department code"),
        "establishment_year": ("Enter the year the department was established.", "Go to Year of establishment"),
    }
    text, action_label = messages.get(
        field_key,
        (f"Complete the required field: {label}.", f"Go to {label}"),
    )
    return {
        "field_key": field_key,
        "label": label,
        "message": text,
        "action_type": "scroll",
        "action_label": action_label,
        "action_href": None,
    }


def _validate_form(
    form: CreateEditDepartmentFormValues,
    *,
    strict: bool,
    school_selectable: int = 0,
    campus_selectable: int = 0,
) -> None:
    if strict:
        missing_keys: list[str] = []
        for key, val in [
            ("name", form.name.strip()),
            ("department_code", form.department_code.strip()),
            ("organization_unit_id", form.organization_unit_id),
            ("campus_id", form.campus_id),
        ]:
            if not val:
                missing_keys.append(key)
        if form.establishment_year is None:
            missing_keys.append("establishment_year")
        if missing_keys:
            details = [
                _validation_detail(key, school_selectable=school_selectable, campus_selectable=campus_selectable)
                for key in missing_keys
            ]
            raise AppError(
                code="VALIDATION_ERROR",
                message="Complete the required fields below before saving.",
                status_code=422,
                details=details,
            )
    elif not form.name.strip() or not form.department_code.strip():
        draft_keys = []
        if not form.name.strip():
            draft_keys.append("name")
        if not form.department_code.strip():
            draft_keys.append("department_code")
        details = [
            _validation_detail(key, school_selectable=school_selectable, campus_selectable=campus_selectable)
            for key in draft_keys
        ]
        raise AppError(
            code="VALIDATION_ERROR",
            message="Department name and code are required to save a draft.",
            status_code=422,
            details=details,
        )


async def save_create_edit_department(
    scope: AccessScope,
    payload: CreateEditDepartmentSavePayload,
) -> CreateEditDepartmentPageRead:
    authorize(scope, Permission.INSTITUTION_ORG_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    form = payload.form
    strict = payload.mode == "create"
    opts = await _load_options(tenant_id, scope)
    school_selectable = sum(1 for row in opts["school_options"] if row.value)
    campus_selectable = sum(1 for row in opts["campus_options"] if row.value)
    _validate_form(
        form,
        strict=strict,
        school_selectable=school_selectable,
        campus_selectable=campus_selectable,
    )

    campus_ids = [form.campus_id] if form.campus_id else []
    status = DepartmentStatus.DRAFT if payload.mode == "draft" or not form.head_user_id else DepartmentStatus.ACTIVE

    if payload.department_id:
        department_oid = to_object_id(payload.department_id, "department_id")
        update_payload = InstitutionDepartmentUpdate(
            name=form.name.strip(),
            description=form.vision_mission.strip() or None,
            department_kind=DepartmentKind(form.department_kind),
            establishment_year=form.establishment_year,
            building_floor_label=form.building_floor_label.strip() or None,
            contact_email=form.contact_email.strip() or None,
            approved_intake_ug=form.approved_intake_ug,
            aicte_approval_reference=form.aicte_approval_reference.strip() or None,
            cost_centre_code=form.cost_centre_code.strip() or None,
            settings_template_department_id=form.settings_template_department_id or None,
            organization_unit_id=form.organization_unit_id or None,
            campus_ids=campus_ids,
            status=status if strict else None,
        )
        await update_institution_department(scope, department_oid, update_payload)
        if form.head_user_id:
            doc = await InstitutionDepartment.get(department_oid)
            if doc and doc.head_user_id != to_object_id(form.head_user_id, "head_user_id"):
                from app.modules.college_admin.identity_schemas import DepartmentHeadAssign

                from app.modules.college_admin.organization_service import assign_department_head

                await assign_department_head(
                    scope,
                    department_oid,
                    DepartmentHeadAssign(user_id=form.head_user_id),
                )
        return await get_create_edit_department_page(scope, department_oid)

    create_payload = InstitutionDepartmentCreate(
        department_code=form.department_code.strip(),
        name=form.name.strip(),
        description=form.vision_mission.strip() or None,
        department_kind=DepartmentKind(form.department_kind),
        establishment_year=form.establishment_year,
        building_floor_label=form.building_floor_label.strip() or None,
        contact_email=form.contact_email.strip() or None,
        approved_intake_ug=form.approved_intake_ug,
        aicte_approval_reference=form.aicte_approval_reference.strip() or None,
        cost_centre_code=form.cost_centre_code.strip() or None,
        settings_template_department_id=form.settings_template_department_id or None,
        head_user_id=form.head_user_id or None,
        organization_unit_id=form.organization_unit_id or None,
        campus_ids=campus_ids,
        status=status,
    )
    created = await create_institution_department(scope, create_payload)
    return await get_create_edit_department_page(scope, to_object_id(created.department_id, "department_id"))


async def get_create_edit_department_page_by_id(scope: AccessScope, department_id_raw: str | None) -> CreateEditDepartmentPageRead:
    department_id = to_object_id(department_id_raw, "department_id") if department_id_raw else None
    return await get_create_edit_department_page(scope, department_id)