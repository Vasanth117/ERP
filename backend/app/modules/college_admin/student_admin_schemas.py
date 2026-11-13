"""Student administration API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.modules.college_admin.student_admin_models import (
    AdmissionStatus,
    StudentAdmission,
    StudentLifecycleStatus,
    StudentRecord,
    TransferStatus,
)
from app.modules.students.enums import StudentEnrollmentStatus


class AdmissionCreate(BaseModel):
    admission_number: str = Field(min_length=4, max_length=32)
    applicant_name: str
    applicant_email: EmailStr
    programme_code: str
    department_id: str | None = None
    batch_label: str | None = None
    academic_year_code: str


class AdmissionRead(BaseModel):
    admission_id: str
    admission_number: str
    applicant_name: str
    programme_code: str
    status: AdmissionStatus
    academic_year_code: str

    @classmethod
    def from_document(cls, doc: StudentAdmission) -> "AdmissionRead":
        return cls(
            admission_id=str(doc.id),
            admission_number=doc.admission_number,
            applicant_name=doc.applicant_name,
            programme_code=doc.programme_code,
            status=doc.status,
            academic_year_code=doc.academic_year_code,
        )


class StudentRecordCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str
    student_id: str | None = None
    roll_number: str | None = None
    admission_id: str | None = None
    department_id: str | None = None
    programme_code: str | None = None
    batch_label: str | None = None
    section_code: str | None = None


class StudentRecordUpdate(BaseModel):
    roll_number: str | None = None
    programme_code: str | None = None
    batch_label: str | None = None
    section_code: str | None = None
    department_id: str | None = None
    contact_phone: str | None = None


class StudentRecordRead(BaseModel):
    record_id: str
    user_id: str
    student_id: str | None
    roll_number: str | None
    full_name: str
    email: str
    programme_code: str | None
    batch_label: str | None
    section_code: str | None
    department_id: str | None
    lifecycle_status: StudentLifecycleStatus
    enrollment_status: StudentEnrollmentStatus

    @classmethod
    def from_parts(cls, record: StudentRecord, *, full_name: str, email: str) -> "StudentRecordRead":
        return cls(
            record_id=str(record.id),
            user_id=str(record.user_id),
            student_id=record.student_id,
            roll_number=record.roll_number,
            full_name=full_name,
            email=email,
            programme_code=record.programme_code,
            batch_label=record.batch_label,
            section_code=record.section_code,
            department_id=str(record.department_id) if record.department_id else None,
            lifecycle_status=record.lifecycle_status,
            enrollment_status=record.enrollment_status,
        )


class StudentStatusChange(BaseModel):
    lifecycle_status: StudentLifecycleStatus
    reason: str | None = Field(default=None, max_length=500)


class EnrollmentAssign(BaseModel):
    academic_year_label: str
    semester_label: str
    course_id: str
    course_code: str
    course_name: str
    section_code: str


class TransferCreate(BaseModel):
    to_department_id: str | None = None
    to_programme_code: str | None = None
    reason: str = Field(max_length=1000)
    effective_date: date | None = None


class PromotionCreate(BaseModel):
    to_academic_year: str
    to_semester: str
    decision: str = Field(max_length=64)


class GuardianCreate(BaseModel):
    guardian_name: str
    relationship: str
    phone: str
    email: EmailStr | None = None
    portal_access_allowed: bool = False


class BulkStudentImport(BaseModel):
    students: list[StudentRecordCreate] = Field(min_length=1, max_length=200)


class ProfileCorrectionDecision(BaseModel):
    request_id: str
    approve: bool
    note: str | None = None


class StudentAcademicHistoryRead(BaseModel):
    status_history: list[dict]
    promotions: list[dict]
    transfers: list[dict]
    enrollments: list[dict]
