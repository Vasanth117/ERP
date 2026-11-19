"""Examination cell — request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.examinations.exam_cell_enums import (
    ExamSessionLifecycleAction,
    ExamSessionStatus,
    ExamSessionType,
)
from app.modules.examinations.exam_cell_models import ExamSession, ExamSessionAcademicScope


class ExamSessionAcademicScopeInput(BaseModel):
    department_codes: list[str] = Field(default_factory=list, max_length=200)
    programme_codes: list[str] = Field(default_factory=list, max_length=200)
    batch_labels: list[str] = Field(default_factory=list, max_length=200)
    semester_labels: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("department_codes", "programme_codes", "batch_labels", "semester_labels")
    @classmethod
    def normalize_codes(cls, value: list[str]) -> list[str]:
        return [v.strip().upper() for v in value if v and v.strip()]


class ExamSessionCreate(BaseModel):
    session_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    examination_type: ExamSessionType = ExamSessionType.REGULAR
    academic_year_label: str = Field(min_length=2, max_length=32)
    semester_label: str = Field(min_length=1, max_length=32)
    season_id: str | None = Field(default=None, max_length=64)
    registration_start_at: datetime
    registration_end_at: datetime
    examination_start_at: datetime
    examination_end_at: datetime
    result_processing_deadline_at: datetime | None = None
    academic_scope: ExamSessionAcademicScopeInput = Field(default_factory=ExamSessionAcademicScopeInput)

    @field_validator("session_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class ExamSessionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    registration_start_at: datetime | None = None
    registration_end_at: datetime | None = None
    examination_start_at: datetime | None = None
    examination_end_at: datetime | None = None
    result_processing_deadline_at: datetime | None = None
    academic_scope: ExamSessionAcademicScopeInput | None = None


class ExamSessionAcademicScopeRead(BaseModel):
    department_codes: list[str]
    programme_codes: list[str]
    batch_labels: list[str]
    semester_labels: list[str]


class ExamSessionRead(BaseModel):
    id: str
    session_id: str
    session_code: str
    name: str
    examination_type: ExamSessionType
    academic_year_label: str
    semester_label: str
    season_id: str | None
    registration_start_at: datetime
    registration_end_at: datetime
    examination_start_at: datetime
    examination_end_at: datetime
    result_processing_deadline_at: datetime | None
    status: ExamSessionStatus
    academic_scope: ExamSessionAcademicScopeRead
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_documents(
        cls,
        session: ExamSession,
        scope: ExamSessionAcademicScope | None,
    ) -> "ExamSessionRead":
        scope_read = ExamSessionAcademicScopeRead(
            department_codes=list(scope.department_codes) if scope else [],
            programme_codes=list(scope.programme_codes) if scope else [],
            batch_labels=list(scope.batch_labels) if scope else [],
            semester_labels=list(scope.semester_labels) if scope else [],
        )
        return cls(
            id=str(session.id),
            session_id=session.session_id,
            session_code=session.session_code,
            name=session.name,
            examination_type=session.examination_type,
            academic_year_label=session.academic_year_label,
            semester_label=session.semester_label,
            season_id=session.season_id,
            registration_start_at=session.registration_start_at,
            registration_end_at=session.registration_end_at,
            examination_start_at=session.examination_start_at,
            examination_end_at=session.examination_end_at,
            result_processing_deadline_at=session.result_processing_deadline_at,
            status=session.status,
            academic_scope=scope_read,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )


class ExamSessionTransitionRequest(BaseModel):
    action: ExamSessionLifecycleAction
    note: str | None = Field(default=None, max_length=500)


class ExamSessionStatusHistoryRead(BaseModel):
    from_status: ExamSessionStatus | None
    to_status: ExamSessionStatus
    actor_id: str | None
    note: str | None
    created_at: datetime


class ExamSessionListFilters(BaseModel):
    academic_year_label: str | None = None
    semester_label: str | None = None
    examination_type: ExamSessionType | None = None
    status: ExamSessionStatus | None = None
    department_code: str | None = None
    course_code: str | None = None
    session_code: str | None = None