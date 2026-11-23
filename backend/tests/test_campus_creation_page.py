"""Campus creation wizard page service."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.campus_creation_page_service import (
    finish_campus_creation,
    get_campus_creation_page,
    save_campus_creation_draft,
)
from app.modules.college_admin.schemas import CampusCreationDraftUpdate, CampusCreationFinishPayload
from app.modules.tenants.models import Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")
    try:
        await connect_redis()
    except Exception:
        pass
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


async def _scope(suffix: str) -> tuple[Tenant, AccessScope]:
    tenant = Tenant(name=f"College CC {suffix}", code=f"cc_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+cc+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    return tenant, scope


@pytest.mark.anyio
async def test_campus_creation_draft_accepts_null_optional_fields(db_ready):
    suffix = uuid4().hex[:8]
    _, scope = await _scope(suffix)
    page = await get_campus_creation_page(scope)
    page = await save_campus_creation_draft(
        scope,
        CampusCreationDraftUpdate(
            draft_id=page.draft_id,
            step_key="identity",
            values={
                "campus_code": "WEST",
                "name": "West Campus",
                "address_line1": None,
                "city": None,
                "country": "India",
            },
            advance=True,
        ),
    )
    assert page.current_step_key == "location"


@pytest.mark.anyio
async def test_campus_creation_draft_retreat_step(db_ready):
    suffix = uuid4().hex[:8]
    _, scope = await _scope(suffix)
    page = await get_campus_creation_page(scope)
    page = await save_campus_creation_draft(
        scope,
        CampusCreationDraftUpdate(
            draft_id=page.draft_id,
            step_key="identity",
            values={"campus_code": "EAST", "name": "East Campus"},
            advance=True,
        ),
    )
    assert page.current_step_key == "location"
    page = await save_campus_creation_draft(
        scope,
        CampusCreationDraftUpdate(
            draft_id=page.draft_id,
            step_key="location",
            values={"city": "Madurai"},
            advance=True,
        ),
    )
    assert page.current_step_key == "contact"
    page = await save_campus_creation_draft(
        scope,
        CampusCreationDraftUpdate(
            draft_id=page.draft_id,
            step_key="contact",
            values=page.form.model_dump(),
            retreat=True,
        ),
    )
    assert page.current_step_key == "location"


@pytest.mark.anyio
async def test_campus_creation_wizard_draft_and_finish(db_ready):
    suffix = uuid4().hex[:8]
    _, scope = await _scope(suffix)

    page = await get_campus_creation_page(scope)
    assert page.draft_id
    assert page.current_step_key == "identity"
    assert len(page.steps) == 6

    page = await save_campus_creation_draft(
        scope,
        CampusCreationDraftUpdate(
            draft_id=page.draft_id,
            step_key="identity",
            values={"campus_code": "NORTH", "name": "North Campus", "country": "India"},
            advance=True,
        ),
    )
    assert page.current_step_key == "location"

    merged = {
        **page.form.model_dump(),
        "address_line1": "12 College Road",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "country": "India",
    }
    page = await save_campus_creation_draft(
        scope,
        CampusCreationDraftUpdate(draft_id=page.draft_id, step_key="location", values=merged, advance=True),
    )
    assert page.current_step_key == "contact"

    result = await finish_campus_creation(
        scope,
        CampusCreationFinishPayload(draft_id=page.draft_id, values=merged),
    )
    assert result.campus_id
    assert "/college-admin/institution/campuses/" in result.detail_href