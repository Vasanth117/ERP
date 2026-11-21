"""Tenant, institution, campuses, departments, academic context."""

from datetime import date, timedelta

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.roles import Role
from app.common.time import utcnow
from app.core.security import hash_password
from app.modules.academics.models import AcademicYearContext
from app.modules.auth.models import User
from app.modules.college_admin.enums import InstitutionActivityKind
from app.modules.college_admin.institution_service import create_campus, update_institution_profile
from app.modules.college_admin.models import (
    InstitutionActivityLog,
    InstitutionBranding,
    InstitutionCampus,
    InstitutionProfile,
    InstitutionSettings,
)
from app.modules.college_admin.rbac_service import seed_tenant_permission_catalog
from app.modules.college_admin.schemas import CampusCreate, InstitutionProfileUpdate
from app.modules.configuration.models import TenantConfiguration, TenantFeatureFlags
from app.modules.demo.constants import (
    DEMO_ACADEMIC_YEAR,
    DEMO_INSTITUTION_EMAIL,
    DEMO_PASSWORD,
    DEMO_SEMESTER,
    DEMO_TENANT_CODE,
    DEMO_TENANT_NAME,
    DEPARTMENTS,
    ROLE_ACCOUNTS,
)
from app.modules.demo.seed.context import DemoSeedContext
from app.modules.subscriptions.enums import SubscriptionStatus
from app.modules.subscriptions.models import PlanEntitlement, SubscriptionPlan, TenantSubscription
from app.modules.tenants.domain_utils import normalize_tenant_code
from app.modules.tenants.models import Department, Tenant
from app.modules.tenants.platform_models import InstitutionAddress


async def _ensure_subscription(tenant_id) -> None:
    plan = await SubscriptionPlan.find_one(Eq(SubscriptionPlan.code, "enterprise"))
    if plan is None:
        return
    existing = await TenantSubscription.find_one(Eq(TenantSubscription.tenant_id, tenant_id))
    if existing is not None:
        return
    now = utcnow()
    await TenantSubscription(
        tenant_id=tenant_id,
        plan_id=plan.id,
        plan_code=plan.code,
        status=SubscriptionStatus.ACTIVE,
        current_period_start=now,
        current_period_end=now + timedelta(days=365),
    ).insert()


async def seed_foundation(*, student_target: int, reset: bool) -> DemoSeedContext:
    code = normalize_tenant_code(DEMO_TENANT_CODE)
    existing = await Tenant.find_one(Eq(Tenant.code, code))
    if existing is not None and reset:
        from app.modules.demo.seed.purge import purge_tenant_completely

        await purge_tenant_completely(existing.id)
        existing = None

    if existing is None:
        tenant = Tenant(
            name=DEMO_TENANT_NAME,
            code=code,
            institution_email=DEMO_INSTITUTION_EMAIL,
            institution_type="engineering_college",
            is_demo=True,
            timezone="Asia/Kolkata",
            locale="en-IN",
            address=InstitutionAddress(
                line1="SVIET Campus, Chennai–Bangalore Highway",
                city="Vellore",
                state="Tamil Nadu",
                country="India",
                postal_code="632001",
            ),
        )
        await tenant.insert()
    else:
        tenant = existing
        tenant.is_demo = True
        tenant.name = DEMO_TENANT_NAME
        await tenant.save()

    await _ensure_subscription(tenant.id)
    await seed_tenant_permission_catalog(tenant.id)

    email = ROLE_ACCOUNTS[0][1].lower()
    admin = await User.find_one(Eq(User.email, email), Eq(User.tenant_id, tenant.id))
    password_hash = hash_password(DEMO_PASSWORD)
    if admin is None:
        admin = User(
            email=email,
            hashed_password=password_hash,
            full_name=ROLE_ACCOUNTS[0][2],
            role=Role.COLLEGE_ADMIN,
            tenant_id=tenant.id,
            is_active=True,
        )
        await admin.insert()
    else:
        admin.hashed_password = password_hash
        admin.is_active = True
        await admin.save()

    admin_scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=admin.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )

    profile = await InstitutionProfile.find_one(Eq(InstitutionProfile.tenant_id, tenant.id))
    if profile is None:
        await update_institution_profile(
            admin_scope,
            InstitutionProfileUpdate(
                legal_name="Sri Venkateswara Institute of Engineering & Technology",
                display_name=DEMO_TENANT_NAME,
                short_name="SVIET",
                institution_code="SVIET-DEMO",
                institution_email=DEMO_INSTITUTION_EMAIL,
                contact_phone="+91-416-290-1000",
                official_website="https://sviet-demo.edu",
                description=(
                    "A fully populated demo college for client presentations — academics, "
                    "finance, HR, hostel, library, and examinations."
                ),
                institution_type="autonomous_engineering_college",
                affiliation_name="Anna University",
                year_established=1998,
                accreditation_display="NAAC A+ | NBA Accredited Programmes",
                address=InstitutionAddress(
                    line1="SVIET Campus, Chennai–Bangalore Highway",
                    city="Vellore",
                    state="Tamil Nadu",
                    country="India",
                    postal_code="632001",
                ),
            ),
        )

    campuses = await InstitutionCampus.find(Eq(InstitutionCampus.tenant_id, tenant.id)).to_list()
    if not campuses:
        main = await create_campus(
            admin_scope,
            CampusCreate(
                campus_code="MAIN",
                name="Main Campus — Vellore",
                is_main=True,
                contact_email="main@sviet-demo.edu",
                contact_phone="+91-416-290-1001",
                area_acres=85,
                buildings_count=24,
                address=InstitutionAddress(city="Vellore", state="Tamil Nadu", country="India"),
            ),
        )
        await create_campus(
            admin_scope,
            CampusCreate(
                campus_code="CITY",
                name="City Learning Centre",
                is_main=False,
                contact_email="city@sviet-demo.edu",
                address=InstitutionAddress(city="Chennai", state="Tamil Nadu", country="India"),
            ),
        )
        main_campus_id = to_object_id(main.campus_id, "campus_id")
    else:
        main_campus = next((c for c in campuses if c.is_main), campuses[0])
        main_campus_id = main_campus.id

    dept_map: dict[str, Department] = {}
    for code, name, _prog, _label in DEPARTMENTS:
        dept = await Department.find_one(Eq(Department.tenant_id, tenant.id), Eq(Department.code, code))
        if dept is None:
            dept = Department(tenant_id=tenant.id, name=name, code=code, is_active=True)
            await dept.insert()
        dept_map[code] = dept

    ctx_row = await AcademicYearContext.find_one(Eq(AcademicYearContext.tenant_id, tenant.id))
    if ctx_row is None:
        today = date.today()
        await AcademicYearContext(
            tenant_id=tenant.id,
            academic_year_label=DEMO_ACADEMIC_YEAR,
            semester_label=DEMO_SEMESTER,
            semester_start=today - timedelta(days=60),
            semester_end=today + timedelta(days=120),
            is_current=True,
        ).insert()

    if await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant.id)) is None:
        await InstitutionSettings(
            tenant_id=tenant.id,
            settings={
                "enabled_modules": [
                    "academics",
                    "students",
                    "faculty",
                    "attendance",
                    "examinations",
                    "finance",
                    "hr",
                    "library",
                    "hostel",
                    "parents",
                ],
                "timezone": "Asia/Kolkata",
                "demo_student_quota": student_target,
            },
            updated_by=admin.id,
        ).insert()

    if await InstitutionBranding.find_one(Eq(InstitutionBranding.tenant_id, tenant.id)) is None:
        await InstitutionBranding(
            tenant_id=tenant.id,
            display_name="SVIET",
            primary_color="#1E3A8A",
            secondary_color="#F59E0B",
            theme={"accent": "#F59E0B", "surface": "#F8FAFC"},
            published_at=utcnow(),
            updated_by=admin.id,
        ).insert()

    if await TenantConfiguration.find_one(Eq(TenantConfiguration.tenant_id, tenant.id)) is None:
        await TenantConfiguration(
            tenant_id=tenant.id,
            settings={"locale": "en-IN", "timezone": "Asia/Kolkata"},
        ).insert()

    flags = await TenantFeatureFlags.find_one(Eq(TenantFeatureFlags.tenant_id, tenant.id))
    if flags is None:
        await TenantFeatureFlags(
            tenant_id=tenant.id,
            flags={
                "attendance_beta": True,
                "finance_v2": True,
                "examination_analytics": True,
                "parent_portal": True,
            },
        ).insert()

    activity_count = await InstitutionActivityLog.find(Eq(InstitutionActivityLog.tenant_id, tenant.id)).count()
    if activity_count < 5:
        samples = [
            ("Student admissions window opened", InstitutionActivityKind.SETTINGS_UPDATED),
            ("November semester timetable published", InstitutionActivityKind.CAMPUS_UPDATED),
            ("Hostel room allocation completed", InstitutionActivityKind.CAMPUS_CREATED),
            ("Finance fee collection milestone reached", InstitutionActivityKind.PROFILE_UPDATED),
        ]
        for summary, kind in samples:
            await InstitutionActivityLog(
                tenant_id=tenant.id,
                actor_id=admin.id,
                activity_kind=kind,
                resource_type="demo_seed",
                resource_id=None,
                summary=summary,
            ).insert()

    ctx = DemoSeedContext(
        tenant=tenant,
        admin=admin,
        admin_scope=admin_scope,
        main_campus_id=main_campus_id,
        departments=dept_map,
    )
    return ctx