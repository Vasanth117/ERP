"""High-volume, batched people seeding for enterprise demo profiles."""

from __future__ import annotations

from datetime import date

from beanie.odm.operators.find.comparison import Eq, In

from app.common.roles import Role
from app.core.security import hash_password
from app.modules.academics.curriculum_models import EnrollmentRosterEntry
from app.modules.auth.models import User
from app.modules.demo.constants import (
    DEMO_ACADEMIC_YEAR,
    DEMO_EMAIL_DOMAIN,
    DEMO_PASSWORD,
    DEMO_SEMESTER,
    DEPARTMENTS,
)
from app.modules.demo.seed.context import DemoSeedContext
from app.modules.students.models import StudentAcademicRecord, StudentProfile

_CHUNK = 400
_FIRST_NAMES = (
    "Aarav",
    "Diya",
    "Vikram",
    "Kavya",
    "Rohan",
    "Ananya",
    "Karthik",
    "Meera",
    "Arjun",
    "Sneha",
    "Harish",
    "Pooja",
    "Naveen",
    "Lakshmi",
    "Gaurav",
    "Divya",
    "Sanjay",
    "Nithya",
    "Rahul",
    "Ishita",
    "Varun",
    "Shreya",
    "Aditya",
    "Keerthana",
)
_LAST_NAMES = (
    "Kumar",
    "Sharma",
    "Iyer",
    "Reddy",
    "Nair",
    "Patel",
    "Singh",
    "Menon",
    "Rao",
    "Pillai",
    "Krishnan",
    "Bala",
    "Selvam",
    "Devi",
)


async def _chunked_insert(model, docs: list) -> None:
    for offset in range(0, len(docs), _CHUNK):
        batch = docs[offset : offset + _CHUNK]
        if batch:
            await model.insert_many(batch)


def demo_password_hash() -> str:
    return hash_password(DEMO_PASSWORD)


def _build_student_batch(
    ctx: DemoSeedContext,
    *,
    start_index: int,
    end_index: int,
    password_hash: str,
) -> tuple[list[User], list[StudentProfile], list[EnrollmentRosterEntry], list[StudentAcademicRecord]]:
    tenant_id = ctx.tenant.id
    dept_codes = [d[0] for d in DEPARTMENTS]
    users: list[User] = []
    profiles: list[StudentProfile] = []
    rosters: list[EnrollmentRosterEntry] = []
    academics: list[StudentAcademicRecord] = []

    for i in range(start_index, end_index):
        dept_code = dept_codes[i % len(dept_codes)]
        dept = ctx.departments[dept_code]
        prog_code = next(p[2] for p in DEPARTMENTS if p[0] == dept_code)
        prog_name = next(p[3] for p in DEPARTMENTS if p[0] == dept_code)
        fname = _FIRST_NAMES[i % len(_FIRST_NAMES)]
        lname = _LAST_NAMES[(i // len(_FIRST_NAMES)) % len(_LAST_NAMES)]
        batch_year = 2018 + (i % 7)
        study_year = min(4, 1 + (i % 4))
        section = chr(ord("A") + (i % 3))
        email = f"student{i+1:05d}@{DEMO_EMAIL_DOMAIN}"
        user = User(
            email=email,
            hashed_password=password_hash,
            full_name=f"{fname} {lname}",
            role=Role.STUDENT,
            tenant_id=tenant_id,
            department_id=dept.id,
            is_active=True,
        )
        users.append(user)
        roll = f"{batch_year % 100}{dept_code}{i+1:04d}"
        profiles.append(
            StudentProfile(
                tenant_id=tenant_id,
                user_id=user.id,
                student_id=f"STU-{i+1:06d}",
                roll_number=roll,
                admission_number=f"ADM-{batch_year}-GHIT-{i+1:05d}",
                admission_date=date(batch_year, 7, 20),
                department_id=dept.id,
                programme_code=prog_code,
                programme_name=prog_name,
                batch_label=str(batch_year),
                section_code=section,
            )
        )
        rosters.append(
            EnrollmentRosterEntry(
                tenant_id=tenant_id,
                course_id=f"{dept_code.lower()}{100 + study_year}",
                course_code=f"{dept_code}{100 + study_year}",
                section_code=section,
                student_user_id=user.id,
                roll_number=roll,
                display_name=f"{fname} {lname}",
                academic_year_label=DEMO_ACADEMIC_YEAR,
                semester_label=DEMO_SEMESTER,
            )
        )
        outstanding = 25_000 + (i % 40) * 750
        paid_pct = 55 + (i % 45)
        academics.append(
            StudentAcademicRecord(
                tenant_id=tenant_id,
                user_id=user.id,
                academic_year_label=DEMO_ACADEMIC_YEAR,
                semester_label=DEMO_SEMESTER,
                fee_snapshot={
                    "status": "partial" if paid_pct < 100 else "paid",
                    "outstanding_amount": outstanding * (100 - paid_pct) // 100,
                    "currency": "INR",
                    "paid_percentage": paid_pct,
                    "current_semester": study_year,
                },
            )
        )
    return users, profiles, rosters, academics


async def bulk_seed_faculty(
    ctx: DemoSeedContext,
    *,
    faculty_count: int,
    password_hash: str,
    start_index: int = 0,
) -> list[User]:
    tenant_id = ctx.tenant.id
    dept_codes = [d[0] for d in DEPARTMENTS]
    new_users: list[User] = []

    for i in range(start_index, faculty_count):
        dept_code = dept_codes[i % len(dept_codes)]
        dept = ctx.departments[dept_code]
        fname = _FIRST_NAMES[i % len(_FIRST_NAMES)]
        lname = _LAST_NAMES[(i // len(_FIRST_NAMES)) % len(_LAST_NAMES)]
        new_users.append(
            User(
                email=f"faculty{i+1:05d}@{DEMO_EMAIL_DOMAIN}",
                hashed_password=password_hash,
                full_name=f"Prof. {fname} {lname}",
                role=Role.FACULTY,
                tenant_id=tenant_id,
                department_id=dept.id,
                is_active=True,
            )
        )

    await _chunked_insert(User, new_users)
    return await User.find(Eq(User.tenant_id, tenant_id), Eq(User.role, Role.FACULTY)).to_list()


async def bulk_seed_students(
    ctx: DemoSeedContext,
    *,
    student_count: int,
    password_hash: str,
    start_index: int = 0,
) -> list[User]:
    for batch_start in range(start_index, student_count, _CHUNK):
        batch_end = min(batch_start + _CHUNK, student_count)
        users, profiles, rosters, academics = _build_student_batch(
            ctx,
            start_index=batch_start,
            end_index=batch_end,
            password_hash=password_hash,
        )
        await User.insert_many(users)
        emails = [user.email for user in users]
        persisted = await User.find(
            Eq(User.tenant_id, ctx.tenant.id),
            In(User.email, emails),
        ).to_list()
        email_to_id = {row.email: row.id for row in persisted}
        for idx, user in enumerate(users):
            user_id = email_to_id[user.email]
            profiles[idx].user_id = user_id
            rosters[idx].student_user_id = user_id
            academics[idx].user_id = user_id
        await StudentProfile.insert_many(profiles)
        await EnrollmentRosterEntry.insert_many(rosters)
        await StudentAcademicRecord.insert_many(academics)

    tenant_id = ctx.tenant.id
    return await User.find(Eq(User.tenant_id, tenant_id), Eq(User.role, Role.STUDENT)).to_list()