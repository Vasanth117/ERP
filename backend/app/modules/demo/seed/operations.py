"""Academics, attendance, finance, hostel, library, and examinations demo data."""

from datetime import date, timedelta
from random import Random

from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.modules.academics.enums import SessionType
from app.modules.academics.models import AcademicYearContext, TimetableEntry
from app.modules.accounts_finance.coa_service import seed_default_chart
from app.modules.accounts_finance.mapping_service import seed_default_mappings
from app.modules.attendance.enums import AttendanceMarkStatus, AttendanceSessionStatus
from app.modules.attendance.models import AttendancePolicyReference, AttendanceRecord, AttendanceSession
from app.modules.demo.constants import DEMO_ACADEMIC_YEAR, DEMO_SEMESTER, DEPARTMENTS, LIBRARY_BOOKS
from app.modules.demo.seed.context import DemoSeedContext
from app.modules.examinations.exam_cell_enums import ExamSessionType
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_schemas import ExamSessionAcademicScopeInput, ExamSessionCreate, ExamSessionTransitionRequest
from app.common.ids import to_object_id
from app.modules.examinations.exam_cell_session_service import create_exam_session, transition_exam_session
from app.modules.examinations.exam_cell_enums import ExamSessionLifecycleAction
from app.modules.hostel.infrastructure_schemas import (
    HostelBedPortalCreate,
    HostelBlockCreate,
    HostelBuildingCreate,
    HostelFloorCreate,
    HostelRoomCreate,
    InstitutionHostelCreate,
)
from app.modules.hostel.infrastructure_service import create_bed, create_block, create_building, create_floor, create_hostel, create_room
from app.modules.library.catalogue_schemas import CatalogueRecordCreate
from app.modules.library.catalogue_service import create_catalogue_record
from app.modules.library.facility_schemas import InstitutionLibraryCreate, LibraryBranchCreate
from app.modules.library.facility_service import create_branch_facility, create_library
from app.modules.library.inventory_schemas import CopyRegisterRequest
from app.modules.library.inventory_service import register_copy
from app.modules.library.inventory_validation import normalize_barcode

_RNG = Random(42)


async def seed_operations(ctx: DemoSeedContext) -> None:
    tenant_id = ctx.tenant.id
    scope = ctx.admin_scope

    if await AttendancePolicyReference.find_one(Eq(AttendancePolicyReference.tenant_id, tenant_id)) is None:
        await AttendancePolicyReference(tenant_id=tenant_id).insert()

    tt_count = await TimetableEntry.find(Eq(TimetableEntry.tenant_id, tenant_id)).count()
    if tt_count == 0 and ctx.faculty_users:
        entries: list[TimetableEntry] = []
        slots = [
            (0, "09:00:00", "10:00:00"),
            (0, "10:15:00", "11:15:00"),
            (1, "09:00:00", "10:00:00"),
            (2, "14:00:00", "15:00:00"),
            (3, "11:15:00", "12:15:00"),
        ]
        for i, faculty in enumerate(ctx.faculty_users[:24]):
            dept_code = DEPARTMENTS[i % len(DEPARTMENTS)][0]
            day, start, end = slots[i % len(slots)]
            entries.append(
                TimetableEntry(
                    tenant_id=tenant_id,
                    faculty_user_id=faculty.id,
                    academic_year_label=DEMO_ACADEMIC_YEAR,
                    semester_label=DEMO_SEMESTER,
                    day_of_week=day,
                    start_time=start,
                    end_time=end,
                    course_code=f"{dept_code}101",
                    course_name=f"{dept_code} Fundamentals",
                    section="A" if i % 2 == 0 else "B",
                    session_type=SessionType.LECTURE,
                    room=f"Block-{dept_code}-{_RNG.randint(101, 320)}",
                )
            )
        await TimetableEntry.insert_many(entries)

    session_count = await AttendanceSession.find(Eq(AttendanceSession.tenant_id, tenant_id)).count()
    if session_count == 0 and ctx.faculty_users and ctx.student_users:
        today = date.today()
        records: list[AttendanceRecord] = []
        for day_offset in range(10):
            session_date = today - timedelta(days=day_offset)
            faculty = ctx.faculty_users[day_offset % len(ctx.faculty_users)]
            dept_code = DEPARTMENTS[day_offset % len(DEPARTMENTS)][0]
            session = AttendanceSession(
                tenant_id=tenant_id,
                faculty_user_id=faculty.id,
                course_id=f"{dept_code.lower()}101",
                course_code=f"{dept_code}101",
                section="A",
                session_date=session_date,
                academic_year_label=DEMO_ACADEMIC_YEAR,
                semester_label=DEMO_SEMESTER,
                status=AttendanceSessionStatus.SUBMITTED,
                submitted_at=utcnow(),
            )
            await session.insert()
            cohort = ctx.student_users[day_offset * 5 : day_offset * 5 + 15]
            for si, student in enumerate(cohort):
                status = AttendanceMarkStatus.PRESENT
                if si % 7 == 0:
                    status = AttendanceMarkStatus.ABSENT
                elif si % 11 == 0:
                    status = AttendanceMarkStatus.LATE
                records.append(
                    AttendanceRecord(
                        tenant_id=tenant_id,
                        session_id=session.id,
                        student_user_id=student.id,
                        status=status,
                    )
                )
        if records:
            await AttendanceRecord.insert_many(records)

    exam_count = await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).count()
    if exam_count == 0:
        from app.authorization.permissions import permissions_for_role
        from app.common.access import AccessScope
        from app.common.roles import Role

        exam_user = ctx.staff_users.get("exam") or ctx.admin
        exam_user_scope = AccessScope(
            role=exam_user.role,
            user_id=exam_user.id,
            tenant_id=tenant_id,
            department_id=None,
            effective_permissions=permissions_for_role(exam_user.role),
        )
        now = utcnow()
        created = await create_exam_session(
            exam_user_scope,
            exam_user,
            ExamSessionCreate(
                session_code="NOV-2025",
                name="November 2025 University Examinations",
                examination_type=ExamSessionType.REGULAR,
                academic_year_label=DEMO_ACADEMIC_YEAR,
                semester_label=DEMO_SEMESTER,
                season_id="nov_2025",
                registration_start_at=now - timedelta(days=30),
                registration_end_at=now - timedelta(days=5),
                examination_start_at=now + timedelta(days=10),
                examination_end_at=now + timedelta(days=22),
                result_processing_deadline_at=now + timedelta(days=45),
                academic_scope=ExamSessionAcademicScopeInput(department_codes=[d[0] for d in DEPARTMENTS]),
            ),
        )
        session_oid = to_object_id(created.id, "exam_session_id")
        for action in (
            ExamSessionLifecycleAction.SCHEDULE,
            ExamSessionLifecycleAction.OPEN_REGISTRATION,
            ExamSessionLifecycleAction.CLOSE_REGISTRATION,
            ExamSessionLifecycleAction.START_EXAMINATIONS,
        ):
            try:
                await transition_exam_session(
                    exam_user_scope,
                    exam_user,
                    session_oid,
                    ExamSessionTransitionRequest(action=action, note="Demo seed"),
                )
            except Exception:
                break

    if await AcademicYearContext.find_one(Eq(AcademicYearContext.tenant_id, tenant_id)) is None:
        pass  # foundation already created

    coa_exists = await seed_default_chart(scope)
    _ = coa_exists
    await seed_default_mappings(scope)

    hostel_scope = ctx.staff_users.get("hostel")
    if hostel_scope is not None:
        from app.authorization.permissions import permissions_for_role
        from app.common.access import AccessScope
        from app.common.roles import Role

        hscope = AccessScope(
            role=Role.HOSTEL_ADMIN,
            user_id=hostel_scope.id,
            tenant_id=tenant_id,
            department_id=None,
            effective_permissions=permissions_for_role(Role.HOSTEL_ADMIN),
        )
        try:
            await create_hostel(
                hscope,
                InstitutionHostelCreate(hostel_code="VH1", name="Vishwakarma Boys Hostel", configured_capacity=400),
            )
            await create_building(hscope, HostelBuildingCreate(hostel_code="VH1", building_code="A", name="Block A"))
            await create_block(hscope, HostelBlockCreate(hostel_code="VH1", building_code="A", block_code="W1", name="Wing 1"))
            await create_floor(
                hscope,
                HostelFloorCreate(hostel_code="VH1", building_code="A", floor_id="F1", floor_number=1, name="First Floor"),
            )
            for room_no in range(101, 106):
                await create_room(
                    hscope,
                    HostelRoomCreate(
                        hostel_code="VH1",
                        building_code="A",
                        block_code="W1",
                        floor_id="F1",
                        room_code=str(room_no),
                        capacity=3,
                        bed_capacity=3,
                    ),
                )
                for bed in range(1, 4):
                    await create_bed(
                        hscope,
                        HostelBedPortalCreate(
                            hostel_code="VH1",
                            building_code="A",
                            block_code="W1",
                            room_code=str(room_no),
                            bed_id=f"{room_no}-B{bed}",
                            bed_label=f"Bed {bed}",
                        ),
                    )
        except Exception:
            pass  # idempotent re-run

    lib_scope = ctx.staff_users.get("library")
    if lib_scope is not None:
        from app.authorization.permissions import permissions_for_role
        from app.common.access import AccessScope
        from app.common.roles import Role

        lscope = AccessScope(
            role=Role.LIBRARIAN,
            user_id=lib_scope.id,
            tenant_id=tenant_id,
            department_id=None,
            effective_permissions=permissions_for_role(Role.LIBRARIAN),
        )
        try:
            await create_library(lscope, InstitutionLibraryCreate(library_code="CENTRAL", name="SVIET Central Library"))
            await create_branch_facility(
                lscope,
                LibraryBranchCreate(library_code="CENTRAL", branch_code="MAIN", name="Main Reading Hall"),
            )
            for book_id, title, authors in LIBRARY_BOOKS:
                await create_catalogue_record(lscope, CatalogueRecordCreate(book_id=book_id, title=title, authors=authors))
                for copy_idx in range(1, 4):
                    barcode = normalize_barcode(f"{book_id}-CP{copy_idx}")
                    await register_copy(
                        lscope,
                        CopyRegisterRequest(
                            book_id=book_id,
                            branch_code="MAIN",
                            barcode=barcode,
                            accession_number=f"ACC-{book_id}-{copy_idx}",
                        ),
                    )
        except Exception:
            pass