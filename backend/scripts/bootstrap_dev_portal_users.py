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
from app.modules.auth.models import User
from app.modules.college_admin.student_admin_models import AdmissionStatus, StudentAdmission, StudentGuardianRelationship
from app.modules.parents.enums import ParentAccountStatus
from app.modules.parents.models import ParentProfile
from app.modules.students.models import EmergencyContact, ProfileDocumentRef, StudentProfile
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
DEMO_SEMESTER = "Odd Semester"
DEMO_SEMESTER_NUMBER = 3
DEMO_DOC_UPLOADED = datetime(2022, 6, 12, 10, 0, 0, tzinfo=timezone.utc)

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
        if existing.semester_number is None:
            existing.semester_number = DEMO_SEMESTER_NUMBER
            await existing.save()
            print(f"set semester_number={DEMO_SEMESTER_NUMBER} on academic context")
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
                programme_code="BTECH-CSE",
                programme_name="B.Tech CSE",
                batch_label="2024",
                section_code="A",
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
                    "batch_display": "2024–2028",
                    "programme_duration_years": 4,
                    "class_advisor_name": "Prof. R. Narayanan",
                    "mentor_name": "Dr. M. Rao",
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