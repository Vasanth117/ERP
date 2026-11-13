"""Faculty & employee administration API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.modules.college_admin.faculty_admin_models import (
    EmployeeRecord,
    FacultyDepartmentAssignment,
    FacultyEmploymentHistory,
    FacultyEmploymentStatus,
    FacultyRecord,
    FacultyTeachingAssignment,
    FacultyWorkloadRecord,
)
from app.modules.faculty.models import QualificationRecord


class FacultyRecordCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str
    employee_id: str | None = None
    faculty_code: str | None = None
    designation: str | None = None
    department_id: str | None = None
    campus_id: str | None = None
    specialization: str | None = None
    employment_type: str | None = None
    joining_date: date | None = None


class FacultyRecordUpdate(BaseModel):
    faculty_code: str | None = None
    designation: str | None = None
    department_id: str | None = None
    campus_id: str | None = None
    specialization: str | None = None
    qualifications: list[QualificationRecord] | None = None
    experience_years: float | None = Field(default=None, ge=0)
    contact_phone: str | None = None
    office_location: str | None = None
    employment_status: FacultyEmploymentStatus | None = None


class FacultyRecordRead(BaseModel):
    record_id: str
    user_id: str
    employee_id: str | None
    faculty_code: str | None
    designation: str | None
    department_id: str | None
    campus_id: str | None
    specialization: str | None
    employment_status: FacultyEmploymentStatus
    full_name: str
    email: str

    @classmethod
    def from_parts(
        cls,
        record: FacultyRecord,
        employee: EmployeeRecord | None,
        *,
        full_name: str,
        email: str,
    ) -> "FacultyRecordRead":
        return cls(
            record_id=str(record.id),
            user_id=str(record.user_id),
            employee_id=employee.employee_id if employee else None,
            faculty_code=record.faculty_code,
            designation=record.designation,
            department_id=str(record.department_id) if record.department_id else None,
            campus_id=str(record.campus_id) if record.campus_id else None,
            specialization=record.specialization,
            employment_status=record.employment_status,
            full_name=full_name,
            email=email,
        )


class DepartmentAssignmentCreate(BaseModel):
    department_id: str
    campus_id: str | None = None
    is_primary: bool = True
    effective_from: date | None = None


class TeachingAssignmentCreate(BaseModel):
    academic_year_label: str
    semester_label: str
    course_code: str
    course_name: str
    section: str
    course_id: str | None = None
    subject_id: str | None = None
    subject_code: str | None = None
    subject_name: str | None = None


class WorkloadAllocate(BaseModel):
    academic_year_label: str
    semester_label: str
    lecture_hours: float = Field(default=0, ge=0)
    lab_hours: float = Field(default=0, ge=0)
    tutorial_hours: float = Field(default=0, ge=0)
    credit_units: float = Field(default=0, ge=0)
    note: str | None = None


class FacultyTransferCreate(BaseModel):
    to_department_id: str
    campus_id: str | None = None
    reason: str = Field(max_length=1000)
    effective_date: date | None = None


class FacultyDocumentCreate(BaseModel):
    label: str
    file_id: str
    document_type: str = "other"


class BulkFacultyImport(BaseModel):
    items: list[FacultyRecordCreate] = Field(max_length=100)


class FacultyHistoryRead(BaseModel):
    employment: list[dict]
    department_assignments: list[dict]
    teaching: list[dict]
    workload: list[dict]
