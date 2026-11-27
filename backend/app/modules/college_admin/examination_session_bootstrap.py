"""Prepare assessment pattern and timetable when an exam session is created."""

from __future__ import annotations

from app.common.access import AccessScope
from app.modules.auth.models import User
from app.modules.college_admin.exam_timetable_management_page_service import regenerate_exam_timetable_page
from app.modules.college_admin.internal_external_assessment_page_service import create_session_assessment_pattern_page
from app.modules.college_admin.schemas import ExamTimetableManagementActionPayload


async def bootstrap_examination_session_preparation(
    scope: AccessScope,
    user: User,
    *,
    session_id: str,
) -> None:
    """Idempotent setup: default assessment pattern and semester timetable from curriculum."""
    _ = user
    await create_session_assessment_pattern_page(scope, session_id=session_id)
    await regenerate_exam_timetable_page(
        scope,
        ExamTimetableManagementActionPayload(session_id=session_id, page=1),
    )