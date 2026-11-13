"""Student LMS API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class LearningMaterialRead(BaseModel):
    id: str
    course_code: str
    section: str | None = None
    unit_no: int | None = None
    material_type: str
    title: str
    file_name: str
    mime_type: str
    size_bytes: int
    recorded_url: str | None = None


class MaterialDownloadRead(BaseModel):
    material_id: str
    download_token: str
    content_type: str
    expires_at: datetime


class CourseAnnouncementRead(BaseModel):
    id: str
    title: str
    body: str
    course_code: str | None = None
    created_at: datetime


class LearningProgressRead(BaseModel):
    course_code: str
    materials_viewed: int
    assignments_submitted: int
    quizzes_completed: int
    last_activity_at: datetime | None = None


class QuizParticipationRead(BaseModel):
    quiz_id: str
    title: str
    course_code: str
    scheduled_at: datetime
    participation_enabled: bool
    message: str | None = None
