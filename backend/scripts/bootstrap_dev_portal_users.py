"""Seed demo student and parent portal users (idempotent, local dev only)."""

import asyncio
from datetime import date, datetime, timedelta, timezone

from beanie.odm.operators.find.comparison import Eq

from app.common.roles import Role
from app.common.time import utcnow
from app.core.database import close_mongo, connect_to_mongo
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.modules.academics.models import AcademicYearContext
from app.modules.college_admin.academic_config_models import (
    AcademicProgramme,
    AcademicRegulation,
    ConfigPublicationStatus,
)
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.models import InstitutionProfile
from app.modules.department_admin.models import DepartmentProfileDetails
from app.modules.auth.models import User
from app.modules.college_admin.student_admin_models import AdmissionStatus, StudentAdmission, StudentGuardianRelationship
from app.modules.parents.enums import ParentAccountStatus
from app.modules.parents.models import ParentProfile
from app.modules.students.enums import (
    AcademicStanding,
    ProgressionStatus,
    StudentEnrollmentStatus,
    StudentTermEnrollmentConfirmationStatus,
)
from app.modules.students.models import (
    EmergencyContact,
    ProfileDocumentRef,
    StudentAcademicRecord,
    StudentEnrollment,
    StudentEnrollmentHistory,
    StudentProfile,
    StudentTermEnrollmentConfirmation,
)
from app.modules.students.student_portal_enums import StudentRecordDocumentCategory
from app.modules.students.student_portal_models import StudentDocumentReference
from app.modules.tenants.domain_utils import normalize_tenant_code
from app.modules.tenants.models import Tenant

DEV_TENANT_CODE = "demo-college"
DEV_STUDENT_ID = "STU-DEMO001"
DEV_STUDENT_EMAIL = "student.demo@demo-college.edu"
DEV_STUDENT_PASSWORD = "StudentDemo123!"
DEV_PARENT_ID = "PAR-DEMO001"
DEV_PARENT_EMAIL = "parent.demo@demo-college.edu"
DEV_PARENT_PASSWORD = "ParentDemo123!"
DEMO_ACADEMIC_YEAR = "2025-26"
DEMO_SEMESTER = "Semester 5"
DEMO_SEMESTER_NUMBER = 5
DEMO_DOC_UPLOADED = datetime(2022, 6, 12, 10, 0, 0, tzinfo=timezone.utc)

# Closed terms for ST 02.03 — Semesters / enrollment history (not the active term).
DEMO_ENROLLMENT_HISTORY_CLOSED: tuple[dict, ...] = (
    {
        "academic_year_label": "2024-25",
        "semester_label": "Semester 1",
        "semester_number": 1,
        "period_label": "Aug 2022 – Jan 2023",
        "credits_earned": 21.0,
        "credits_required": 21.0,
        "cgpa": 7.82,
        "closed_at": datetime(2024, 12, 15, 12, 0, 0, tzinfo=timezone.utc),
    },
    {
        "academic_year_label": "2024-25",
        "semester_label": "Semester 2",
        "semester_number": 2,
        "period_label": "Feb – Jun 2023",
        "credits_earned": 22.0,
        "credits_required": 22.0,
        "cgpa": 8.04,
        "closed_at": datetime(2025, 5, 28, 12, 0, 0, tzinfo=timezone.utc),
    },
    {
        "academic_year_label": DEMO_ACADEMIC_YEAR,
        "semester_label": "Semester 3",
        "semester_number": 3,
        "period_label": "Aug 2023 – Jan 2024",
        "credits_earned": 23.0,
        "credits_required": 23.0,
        "cgpa": 8.15,
        "closed_at": datetime(2025, 12, 12, 12, 0, 0, tzinfo=timezone.utc),
    },
    {
        "academic_year_label": DEMO_ACADEMIC_YEAR,
        "semester_label": "Semester 4",
        "semester_number": 4,
        "period_label": "Feb – Jun 2025",
        "credits_earned": 22.0,
        "credits_required": 22.0,
        "cgpa": 8.35,
        "closed_at": datetime(2026, 5, 22, 12, 0, 0, tzinfo=timezone.utc),
    },
)

DEMO_STUDENT_RECORD_DOCUMENTS: tuple[dict, ...] = (
    {
        "document_id": "std-rec-photo-001",
        "document_type": "photo",
        "title": "Photo",
        "category": StudentRecordDocumentCategory.IDENTITY.value,
        "file_format": "JPG",
        "storage_token": "demo:student-photo.jpg",
    },
    {
        "document_id": "std-rec-aadhaar-001",
        "document_type": "aadhaar",
        "title": "Aadhaar card",
        "category": StudentRecordDocumentCategory.IDENTITY.value,
        "file_format": "PDF",
        "storage_token": "demo:aadhaar-card.pdf",
    },
    {
        "document_id": "std-rec-ms10-001",
        "document_type": "marksheet_10",
        "title": "10th marksheet",
        "category": StudentRecordDocumentCategory.ACADEMIC.value,
        "file_format": "PDF",
        "storage_token": "demo:10th-marksheet.pdf",
    },
    {
        "document_id": "std-rec-ms12-001",
        "document_type": "marksheet_12",
        "title": "12th marksheet",
        "category": StudentRecordDocumentCategory.ACADEMIC.value,
        "file_format": "PDF",
        "storage_token": "demo:12th-marksheet.pdf",
    },
    {
        "document_id": "std-rec-tc-001",
        "document_type": "transfer_certificate",
        "title": "Transfer certificate",
        "category": StudentRecordDocumentCategory.ADMISSION.value,
        "file_format": "PDF",
        "storage_token": "demo:transfer-certificate.pdf",
    },
    {
        "document_id": "std-rec-cc-001",
        "document_type": "conduct_certificate",
        "title": "Conduct certificate",
        "category": StudentRecordDocumentCategory.ADMISSION.value,
        "file_format": "PDF",
        "storage_token": "demo:conduct-certificate.pdf",
    },
    {
        "document_id": "std-rec-comm-001",
        "document_type": "community_certificate",
        "title": "Community certificate",
        "category": StudentRecordDocumentCategory.IDENTITY.value,
        "file_format": "PDF",
        "storage_token": "demo:community-certificate.pdf",
    },
    {
        "document_id": "std-rec-admlet-001",
        "document_type": "admission_letter",
        "title": "Provisional admission letter",
        "category": StudentRecordDocumentCategory.ADMISSION.value,
        "file_format": "PDF",
        "storage_token": "demo:admission-letter.pdf",
    },
)


async def _ensure_user(
    *,
    tenant_id,
    email: str,
    password: str,
    full_name: str,
    role: Role,
) -> User:
    email = email.lower()
    user = await User.find_one(Eq(User.email, email), Eq(User.tenant_id, tenant_id))
    password_hash = hash_password(password)
    if user is None:
        user = User(
            email=email,
            hashed_password=password_hash,
            full_name=full_name,
            role=role,
            tenant_id=tenant_id,
            is_active=True,
        )
        await user.insert()
        print(f"created user {email} ({role.value})")
    else:
        user.hashed_password = password_hash
        user.role = role
        user.full_name = full_name
        user.is_active = True
        user.updated_at = utcnow()
        await user.save()
        print(f"updated user {email} ({role.value})")
    return user


async def _ensure_academic_context(tenant_id) -> None:
    existing = await AcademicYearContext.find_one(
        Eq(AcademicYearContext.tenant_id, tenant_id),
        Eq(AcademicYearContext.is_current, True),
    )
    today = date.today()
    if existing is not None:
        existing.academic_year_label = DEMO_ACADEMIC_YEAR
        existing.semester_label = DEMO_SEMESTER
        existing.semester_number = DEMO_SEMESTER_NUMBER
        existing.updated_at = utcnow()
        await existing.save()
        print(f"synced academic context to {DEMO_ACADEMIC_YEAR} / {DEMO_SEMESTER} (sem {DEMO_SEMESTER_NUMBER})")
        return
    await AcademicYearContext(
        tenant_id=tenant_id,
        academic_year_label=DEMO_ACADEMIC_YEAR,
        semester_label=DEMO_SEMESTER,
        semester_number=DEMO_SEMESTER_NUMBER,
        semester_start=today - timedelta(days=60),
        semester_end=today + timedelta(days=120),
        is_current=True,
    ).insert()
    print(f"created academic year context {DEMO_ACADEMIC_YEAR} / sem {DEMO_SEMESTER_NUMBER}")


async def _ensure_programme_department_demo_data(tenant_id) -> None:
    """ST 02.03 / 02.08 — institution, programme, department contacts, progression policy."""
    profile = await InstitutionProfile.find_one(Eq(InstitutionProfile.tenant_id, tenant_id))
    if profile is None:
        await InstitutionProfile(
            tenant_id=tenant_id,
            legal_name="Northbridge College of Engineering",
            display_name="Northbridge College",
            affiliation_name="Anna University",
            accreditation_display="NBA accredited",
        ).insert()
    else:
        profile.affiliation_name = profile.affiliation_name or "Anna University"
        profile.accreditation_display = profile.accreditation_display or "NBA accredited"
        profile.updated_at = utcnow()
        await profile.save()

    programme = await AcademicProgramme.find_one(
        Eq(AcademicProgramme.tenant_id, tenant_id),
        Eq(AcademicProgramme.programme_code, "B.E. CSE"),
    )
    if programme is None:
        await AcademicProgramme(
            tenant_id=tenant_id,
            programme_code="B.E. CSE",
            name="B.E. Computer Science and Engineering",
            duration_semesters=8,
            credits_required=160,
            status=ConfigPublicationStatus.PUBLISHED,
        ).insert()

    regulation = await AcademicRegulation.find_one(
        {"tenant_id": tenant_id, "scope_key": "progression", "status": ConfigPublicationStatus.PUBLISHED},
    )
    if regulation is None:
        await AcademicRegulation(
            tenant_id=tenant_id,
            scope_key="progression",
            status=ConfigPublicationStatus.PUBLISHED,
            rules={
                "min_attendance_percent": 75,
                "max_arrears_carried_label": "Per regulation R2022",
                "completed_semester_requirement": "Pass all",
            },
        ).insert()

    dept = await InstitutionDepartment.find_one(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.name, "Computer Science & Engineering"),
    )
    if dept is None:
        dept = await InstitutionDepartment(
            tenant_id=tenant_id,
            department_code="CSE",
            name="Computer Science & Engineering",
            programme_codes=["B.E. CSE", "BTECH-CSE"],
            contact_email="cse@northbridge.edu",
            building_floor_label="Block A - Room 104",
        ).insert()
    details = await DepartmentProfileDetails.find_one(
        Eq(DepartmentProfileDetails.tenant_id, tenant_id),
        Eq(DepartmentProfileDetails.institution_department_id, dept.id),
    )
    if details is None:
        await DepartmentProfileDetails(
            tenant_id=tenant_id,
            institution_department_id=dept.id,
            central_department_id=dept.central_department_id or dept.id,
            contact_email="cse@northbridge.edu",
            contact_phone="044 2345 6781",
            office_location="Block A - Room 104",
        ).insert()
    else:
        details.contact_email = details.contact_email or "cse@northbridge.edu"
        details.contact_phone = details.contact_phone or "044 2345 6781"
        details.office_location = details.office_location or "Block A - Room 104"
        details.updated_at = utcnow()
        await details.save()


async def main() -> None:
    configure_logging()
    await connect_to_mongo()
    try:
        code = normalize_tenant_code(DEV_TENANT_CODE)
        tenant = await Tenant.find_one(Eq(Tenant.code, code))
        if tenant is None:
            print(f"tenant {code} missing — run bootstrap_dev_college_admin.py first")
            return

        await _ensure_academic_context(tenant.id)
        await _ensure_programme_department_demo_data(tenant.id)

        student = await _ensure_user(
            tenant_id=tenant.id,
            email=DEV_STUDENT_EMAIL,
            password=DEV_STUDENT_PASSWORD,
            full_name="Demo Student",
            role=Role.STUDENT,
        )
        parent = await _ensure_user(
            tenant_id=tenant.id,
            email=DEV_PARENT_EMAIL,
            password=DEV_PARENT_PASSWORD,
            full_name="Demo Parent",
            role=Role.PARENT,
        )

        student_profile = await StudentProfile.find_one(
            Eq(StudentProfile.tenant_id, tenant.id),
            Eq(StudentProfile.user_id, student.id),
        )
        if student_profile is None:
            student_profile = StudentProfile(
                tenant_id=tenant.id,
                user_id=student.id,
                student_id=DEV_STUDENT_ID,
                roll_number="24CSE001",
                admission_number="ADM-2024-001",
                programme_code="B.E. CSE",
                programme_name="B.E. Computer Science and Engineering",
                batch_label="2024",
                section_code="A",
                admission_date=date(2024, 7, 15),
                contact_phone="+91 98400 12345",
                alternate_contact_phone="+91 98400 67890",
                alternate_email="student.demo.personal@mail.com",
                permanent_address="12, Lake View Road, Kochi, Kerala 682016",
                current_address="Kaveri Hostel, B-214, Northbridge College",
                emergency_contacts=[
                    EmergencyContact(name="Demo Parent", phone="+91 98470 11223", relationship="Father"),
                ],
            )
            await student_profile.insert()
            print(f"created student profile {DEV_STUDENT_ID}")
        else:
            student_profile.student_id = DEV_STUDENT_ID
            student_profile.roll_number = student_profile.roll_number or "24CSE001"
            student_profile.admission_number = student_profile.admission_number or "ADM-2024-001"
            student_profile.programme_name = "B.E. Computer Science and Engineering"
            student_profile.programme_code = "B.E. CSE"
            student_profile.contact_phone = student_profile.contact_phone or "+91 98400 12345"
            student_profile.alternate_contact_phone = student_profile.alternate_contact_phone or "+91 98400 67890"
            student_profile.alternate_email = student_profile.alternate_email or "student.demo.personal@mail.com"
            student_profile.permanent_address = (
                student_profile.permanent_address or "12, Lake View Road, Kochi, Kerala 682016"
            )
            student_profile.current_address = (
                student_profile.current_address or "Kaveri Hostel, B-214, Northbridge College"
            )
            if not student_profile.emergency_contacts:
                student_profile.emergency_contacts = [
                    EmergencyContact(name="Demo Parent", phone="+91 98470 11223", relationship="Father"),
                ]
            student_profile.updated_at = utcnow()
            await student_profile.save()
            print(f"updated student profile {DEV_STUDENT_ID}")

        profile_refs = [
            ProfileDocumentRef(
                label=row["title"],
                file_id=row["document_id"],
                document_type=row["document_type"],
                authorized=True,
            )
            for row in DEMO_STUDENT_RECORD_DOCUMENTS
        ]
        if student_profile.document_refs != profile_refs:
            student_profile.document_refs = profile_refs
            student_profile.updated_at = utcnow()
            await student_profile.save()
            print(f"synced {len(profile_refs)} profile document refs")

        for row in DEMO_STUDENT_RECORD_DOCUMENTS:
            existing_doc = await StudentDocumentReference.find_one(
                Eq(StudentDocumentReference.tenant_id, tenant.id),
                Eq(StudentDocumentReference.user_id, student.id),
                Eq(StudentDocumentReference.document_id, row["document_id"]),
            )
            if existing_doc is None:
                await StudentDocumentReference(
                    tenant_id=tenant.id,
                    user_id=student.id,
                    document_id=row["document_id"],
                    document_type=row["document_type"],
                    title=row["title"],
                    category=row["category"],
                    file_format=row["file_format"],
                    verified=True,
                    uploaded_at=DEMO_DOC_UPLOADED,
                    authorized=True,
                    storage_token=row["storage_token"],
                ).insert()
            else:
                existing_doc.title = row["title"]
                existing_doc.category = row["category"]
                existing_doc.file_format = row["file_format"]
                existing_doc.verified = True
                existing_doc.uploaded_at = DEMO_DOC_UPLOADED
                existing_doc.authorized = True
                existing_doc.storage_token = row["storage_token"]
                existing_doc.updated_at = utcnow()
                await existing_doc.save()
        print(f"seeded {len(DEMO_STUDENT_RECORD_DOCUMENTS)} student record documents")

        admission = await StudentAdmission.find_one(
            Eq(StudentAdmission.tenant_id, tenant.id),
            Eq(StudentAdmission.admission_number, "ADM-2024-001"),
        )
        if admission is None:
            await StudentAdmission(
                tenant_id=tenant.id,
                admission_number="ADM-2024-001",
                applicant_name="Aarav Menon",
                applicant_email=student.email,
                programme_code="BTECH-CSE",
                batch_label="2024",
                academic_year_code=DEMO_ACADEMIC_YEAR,
                status=AdmissionStatus.CONFIRMED,
                confirmed_user_id=student.id,
                metadata={
                    "gender": "male",
                    "date_of_birth": "2004-03-14",
                    "nationality": "Indian",
                    "mother_tongue": "Malayalam",
                    "blood_group": "B+",
                    "religion": "Hindu",
                    "community": "BC",
                    "aadhaar": "123412344821",
                    "identity_verified": True,
                    "regulation_label": "R2022",
                    "admission_type": "Counselling · Merit",
                    "study_mode": "Full time",
                    "batch_display": "2024–2028",
                    "programme_duration_years": 4,
                    "class_advisor_name": "Prof. R. Narayanan",
                    "mentor_name": "Dr. M. Rao",
                    "affiliation_name": "Anna University",
                    "accreditation_label": "NBA accredited",
                },
            ).insert()
            print("created student admission with official personal metadata")
        else:
            admission.confirmed_user_id = student.id
            admission.applicant_name = admission.applicant_name or "Aarav Menon"
            admission.status = AdmissionStatus.CONFIRMED
            admission.updated_at = utcnow()
            merged = {**admission.metadata}
            for key, value in {
                "regulation_label": "R2022",
                "admission_type": "Counselling · Merit",
                "batch_display": "2024–2028",
                "programme_duration_years": 4,
                "class_advisor_name": "Prof. R. Narayanan",
                "mentor_name": "Dr. M. Rao",
            }.items():
                merged.setdefault(key, value)
            admission.metadata = merged
            await admission.save()

        guardians = [
            ("father", "Mr. K. Menon", "+91 98470 11223", "k.menon@mail.com", "Engineer"),
            ("mother", "Mrs. L. Menon", "+91 98470 44556", "l.menon@mail.com", "Teacher"),
        ]
        for relationship, name, phone, email, occupation in guardians:
            existing = await StudentGuardianRelationship.find_one(
                Eq(StudentGuardianRelationship.tenant_id, tenant.id),
                Eq(StudentGuardianRelationship.user_id, student.id),
                Eq(StudentGuardianRelationship.guardian_name, name),
            )
            if existing is None:
                await StudentGuardianRelationship(
                    tenant_id=tenant.id,
                    user_id=student.id,
                    guardian_name=name,
                    relationship=relationship,
                    phone=phone,
                    email=email,
                    occupation=occupation,
                ).insert()
            else:
                existing.phone = phone
                existing.email = email
                existing.occupation = occupation
                existing.updated_at = utcnow()
                await existing.save()

        parent_profile = await ParentProfile.find_one(
            Eq(ParentProfile.tenant_id, tenant.id),
            Eq(ParentProfile.user_id, parent.id),
        )
        if parent_profile is None:
            parent_profile = ParentProfile(
                tenant_id=tenant.id,
                user_id=parent.id,
                parent_id=DEV_PARENT_ID,
                display_name="Demo Parent",
                account_status=ParentAccountStatus.ACTIVE,
                email_verified=True,
                mobile_verified=True,
                identity_verified=True,
                activated_at=utcnow(),
            )
            await parent_profile.insert()
            print(f"created parent profile {DEV_PARENT_ID}")
        else:
            parent_profile.parent_id = DEV_PARENT_ID
            parent_profile.account_status = ParentAccountStatus.ACTIVE
            parent_profile.email_verified = True
            parent_profile.updated_at = utcnow()
            await parent_profile.save()
            print(f"updated parent profile {DEV_PARENT_ID}")

        academic_record = await StudentAcademicRecord.find_one(
            Eq(StudentAcademicRecord.tenant_id, tenant.id),
            Eq(StudentAcademicRecord.user_id, student.id),
            Eq(StudentAcademicRecord.academic_year_label, DEMO_ACADEMIC_YEAR),
            Eq(StudentAcademicRecord.semester_label, DEMO_SEMESTER),
        )
        if academic_record is None:
            await StudentAcademicRecord(
                tenant_id=tenant.id,
                user_id=student.id,
                academic_year_label=DEMO_ACADEMIC_YEAR,
                semester_label=DEMO_SEMESTER,
                enrollment_status=StudentEnrollmentStatus.ACTIVE,
                academic_standing=AcademicStanding.GOOD,
                progression_status=ProgressionStatus.PROMOTED,
                promotion_eligible=True,
                credits_registered=20.0,
                credits_earned=88.0,
                cgpa=8.52,
                fee_snapshot={"outstanding_amount": 0, "status": "cleared", "currency": "INR"},
                eligibility_summary={
                    "minimum_credits_required": 160,
                    "credits_completed": 88,
                    "semesters_completed": 4,
                    "total_semesters": 8,
                    "internal_tests_completed": 2,
                    "internal_tests_total": 3,
                    "aggregate_attendance_percent": 86.4,
                    "academic_status_subtitle": "Standing, holds and requirements",
                    "disciplinary_action_label": "None",
                    "academic_holds_label": "None",
                    "backlogs_count": 0,
                    "pending_requirements": [
                        {
                            "title": "Computer Networks attendance",
                            "detail": "72% (need 75%)",
                            "status_label": "Action",
                            "status_tone": "warning",
                            "icon_tone": "alert",
                            "action_href": "/student/timetable/attendance",
                        },
                        {
                            "title": "Mandatory course: Environmental Studies",
                            "detail": "Pending",
                            "status_label": "Open",
                            "status_tone": "info",
                            "icon_tone": "info",
                            "action_href": "/student/academics/eligibility",
                        },
                    ],
                    "next_exam_label": "Internal 3",
                    "next_exam_date_label": "24 Nov",
                    "enrollment_target_semester_number": 6,
                    "enrollment_target_academic_year_label": DEMO_ACADEMIC_YEAR,
                    "enrollment_target_semester_label": "Semester 6",
                    "enrollment_window_opens_at": "2026-12-20T00:00:00+00:00",
                    "enrollment_window_closes_at": "2027-01-31T23:59:59+00:00",
                    "enrollment_window_notice": "You will be able to confirm after Semester 5 results are published.",
                    "enrollment_eligibility_label": "Pending Semester 5 results",
                    "student_enrollment_declaration_accepted": False,
                    "credit_by_category": [
                        {
                            "category": "Basic sciences",
                            "required": 24,
                            "earned": 24,
                            "in_progress": 0,
                            "remaining": 0,
                        },
                        {
                            "category": "Engineering core",
                            "required": 54,
                            "earned": 40,
                            "in_progress": 8,
                            "remaining": 6,
                        },
                        {
                            "category": "Professional core",
                            "required": 56,
                            "earned": 24,
                            "in_progress": 8,
                            "remaining": 24,
                        },
                        {
                            "category": "Electives",
                            "required": 18,
                            "earned": 0,
                            "in_progress": 3,
                            "remaining": 15,
                        },
                        {
                            "category": "Mandatory courses",
                            "required": 8,
                            "earned": 0,
                            "in_progress": 1,
                            "remaining": 7,
                        },
                    ],
                },
            ).insert()
            print("seeded student academic record (Sem 5, 88 credits earned)")
        else:
            academic_record.credits_registered = 20.0
            academic_record.credits_earned = 88.0
            academic_record.cgpa = 8.52
            academic_record.promotion_eligible = True
            academic_record.fee_snapshot = {
                "outstanding_amount": 0,
                "status": "cleared",
                "currency": "INR",
            }
            merged_summary = {**(academic_record.eligibility_summary or {}), **{
                "internal_tests_completed": 2,
                "internal_tests_total": 3,
                "aggregate_attendance_percent": 86.4,
                "academic_status_subtitle": "Standing, holds and requirements",
                "disciplinary_action_label": "None",
                "academic_holds_label": "None",
                "backlogs_count": 0,
                "pending_requirements": [
                    {
                        "title": "Computer Networks attendance",
                        "detail": "72% (need 75%)",
                        "status_label": "Action",
                        "status_tone": "warning",
                        "icon_tone": "alert",
                        "action_href": "/student/timetable/attendance",
                    },
                    {
                        "title": "Mandatory course: Environmental Studies",
                        "detail": "Pending",
                        "status_label": "Open",
                        "status_tone": "info",
                        "icon_tone": "info",
                        "action_href": "/student/academics/eligibility",
                    },
                ],
                "next_exam_label": "Internal 3",
                "next_exam_date_label": "24 Nov",
                "enrollment_target_semester_number": 6,
                "enrollment_target_academic_year_label": DEMO_ACADEMIC_YEAR,
                "enrollment_target_semester_label": "Semester 6",
                "enrollment_window_opens_at": "2026-12-20T00:00:00+00:00",
                "enrollment_window_closes_at": "2027-01-31T23:59:59+00:00",
                "enrollment_window_notice": "You will be able to confirm after Semester 5 results are published.",
                "enrollment_eligibility_label": "Pending Semester 5 results",
                "student_enrollment_declaration_accepted": False,
                "credit_by_category": [
                    {
                        "category": "Basic sciences",
                        "required": 24,
                        "earned": 24,
                        "in_progress": 0,
                        "remaining": 0,
                    },
                    {
                        "category": "Engineering core",
                        "required": 54,
                        "earned": 40,
                        "in_progress": 8,
                        "remaining": 6,
                    },
                    {
                        "category": "Professional core",
                        "required": 56,
                        "earned": 24,
                        "in_progress": 8,
                        "remaining": 24,
                    },
                    {
                        "category": "Electives",
                        "required": 18,
                        "earned": 0,
                        "in_progress": 3,
                        "remaining": 15,
                    },
                    {
                        "category": "Mandatory courses",
                        "required": 8,
                        "earned": 0,
                        "in_progress": 1,
                        "remaining": 7,
                    },
                ],
            }}
            academic_record.eligibility_summary = merged_summary
            academic_record.updated_at = utcnow()
            await academic_record.save()

        demo_subjects = [
            ("CS3501", "Compiler Design", "Theory", 4.0, "Dr. M. Rao"),
            ("CS3591", "Computer Networks", "Theory", 4.0, "Dr. T. Iyer"),
            ("CS3551", "Distributed Systems", "Theory", 3.0, "Prof. R. Narayanan"),
            ("CS3401", "Database Management Systems", "Theory", 4.0, "Prof. R. Narayanan"),
            ("CS3511", "Networks Laboratory", "Lab", 2.0, "Dr. T. Iyer"),
            ("CS3E01", "Machine Learning", "Elective", 3.0, "Dr. A. Kumar"),
        ]
        for code, name, category, credits, faculty in demo_subjects:
            existing_enrollment = await StudentEnrollment.find_one(
                Eq(StudentEnrollment.tenant_id, tenant.id),
                Eq(StudentEnrollment.user_id, student.id),
                Eq(StudentEnrollment.academic_year_label, DEMO_ACADEMIC_YEAR),
                Eq(StudentEnrollment.semester_label, DEMO_SEMESTER),
                Eq(StudentEnrollment.course_code, code),
            )
            if existing_enrollment is None:
                await StudentEnrollment(
                    tenant_id=tenant.id,
                    user_id=student.id,
                    academic_year_label=DEMO_ACADEMIC_YEAR,
                    semester_label=DEMO_SEMESTER,
                    course_id=code.lower(),
                    course_code=code,
                    course_name=name,
                    section_code="A",
                    status=StudentEnrollmentStatus.ACTIVE,
                    category=category,
                    credits=credits,
                    faculty_name=faculty,
                    approved_at=utcnow(),
                ).insert()
            else:
                existing_enrollment.course_name = name
                existing_enrollment.category = category
                existing_enrollment.credits = credits
                existing_enrollment.faculty_name = faculty
                await existing_enrollment.save()
        print("seeded/synced 6 demo registered subjects for Semester 5")

        programme_code = student_profile.programme_code or "BTECH-CSE"
        section_code = student_profile.section_code or "A"
        for term in DEMO_ENROLLMENT_HISTORY_CLOSED:
            existing_hist = await StudentEnrollmentHistory.find_one(
                Eq(StudentEnrollmentHistory.tenant_id, tenant.id),
                Eq(StudentEnrollmentHistory.user_id, student.id),
                Eq(StudentEnrollmentHistory.academic_year_label, term["academic_year_label"]),
                Eq(StudentEnrollmentHistory.semester_label, term["semester_label"]),
            )
            if existing_hist is None:
                await StudentEnrollmentHistory(
                    tenant_id=tenant.id,
                    user_id=student.id,
                    academic_year_label=term["academic_year_label"],
                    semester_label=term["semester_label"],
                    semester_number=term.get("semester_number"),
                    period_label=term.get("period_label"),
                    programme_code=programme_code,
                    section_code=section_code,
                    courses=[],
                    final_standing=AcademicStanding.GOOD,
                    credits_earned=term["credits_earned"],
                    credits_required=term.get("credits_required"),
                    cgpa=term["cgpa"],
                    closed_at=term["closed_at"],
                ).insert()
            else:
                existing_hist.credits_earned = term["credits_earned"]
                existing_hist.credits_required = term.get("credits_required")
                existing_hist.semester_number = term.get("semester_number")
                existing_hist.period_label = term.get("period_label")
                existing_hist.cgpa = term["cgpa"]
                existing_hist.closed_at = term["closed_at"]
                existing_hist.final_standing = AcademicStanding.GOOD
                await existing_hist.save()
        print(f"seeded {len(DEMO_ENROLLMENT_HISTORY_CLOSED)} closed enrollment history terms")

        study_mode = "Full-time"
        demo_confirmations = [
            (1, "2022-23", "Semester 1", datetime(2022, 8, 15, tzinfo=timezone.utc)),
            (2, "2022-23", "Semester 2", datetime(2023, 1, 10, tzinfo=timezone.utc)),
            (3, "2023-24", "Semester 3", datetime(2023, 8, 12, tzinfo=timezone.utc)),
            (4, "2024-25", "Semester 4", datetime(2024, 8, 18, tzinfo=timezone.utc)),
        ]
        for sem_num, ay, sem_label, confirmed_at in demo_confirmations:
            existing_conf = await StudentTermEnrollmentConfirmation.find_one(
                Eq(StudentTermEnrollmentConfirmation.tenant_id, tenant.id),
                Eq(StudentTermEnrollmentConfirmation.user_id, student.id),
                Eq(StudentTermEnrollmentConfirmation.academic_year_label, ay),
                Eq(StudentTermEnrollmentConfirmation.semester_label, sem_label),
            )
            if existing_conf is None:
                await StudentTermEnrollmentConfirmation(
                    tenant_id=tenant.id,
                    user_id=student.id,
                    academic_year_label=ay,
                    semester_label=sem_label,
                    semester_number=sem_num,
                    study_mode=study_mode,
                    status=StudentTermEnrollmentConfirmationStatus.CONFIRMED,
                    eligibility_label="Eligible",
                    confirmed_at=confirmed_at,
                ).insert()
        print(f"seeded up to {len(demo_confirmations)} term enrollment confirmations")

        print()
        print("--- Dev portal users (local only) ---")
        print(f"College code:  {DEV_TENANT_CODE}")
        print(f"Student id:    {DEV_STUDENT_ID}")
        print(f"Student pass:  {DEV_STUDENT_PASSWORD}")
        print(f"Parent id:     {DEV_PARENT_ID}")
        print(f"Parent pass:   {DEV_PARENT_PASSWORD}")
        print("-------------------------------------")
    finally:
        await close_mongo()


if __name__ == "__main__":
    asyncio.run(main())