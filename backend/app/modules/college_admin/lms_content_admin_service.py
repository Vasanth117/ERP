"""College admin LMS content uploads and CSV exports (CA 15.04–06)."""

from __future__ import annotations

import csv
import io

from beanie.odm.operators.find.comparison import Eq
from fastapi import UploadFile

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.college_admin.lms_content_page_service import (
    _VIDEO_MATERIAL_TYPES,
    _date_label,
    _duration_label,
    _faculty_names,
    _material_status,
    _publishing_requires_approval,
    _type_label,
    _video_status,
)
from app.modules.college_admin.lms_unit_chapter_page_service import get_lms_unit_chapter_management_page
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.faculty.course_access import resolve_course_id
from app.modules.lms import storage as lms_storage
from app.modules.lms.enums import MaterialPublishState
from app.modules.lms.models import LearningMaterial


async def upload_lms_content_material(
    scope: AccessScope,
    user: User,
    *,
    course_code: str,
    title: str,
    upload: UploadFile,
    unit_no: int | None = None,
    material_kind: str = "document",
) -> dict:
    authorize(scope, Permission.LMS_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = course_code.strip().upper()
    if not code:
        raise ValueError("course_code is required")
    label = title.strip()
    if not label:
        raise ValueError("title is required")

    course_id = await resolve_course_id(tenant_id, code)
    file_name = upload.filename or "upload.bin"
    mime = upload.content_type or "application/octet-stream"
    raw = await upload.read()
    lms_storage.validate_upload(file_name, mime, len(raw))
    storage_key, checksum = lms_storage.write_bytes(
        lms_storage.storage_key_for(str(tenant_id), "materials", file_name),
        raw,
    )
    kind = (material_kind or "document").strip().lower()
    material_type = "video" if kind in {"video", "recording"} else "document"

    doc = LearningMaterial(
        tenant_id=tenant_id,
        faculty_user_id=user.id,
        course_id=course_id,
        course_code=code,
        unit_no=unit_no,
        material_type=material_type,
        title=label,
        file_id=checksum,
        storage_key=storage_key,
        file_name=file_name,
        mime_type=mime,
        size_bytes=len(raw),
        publish_state=MaterialPublishState.PUBLISHED,
    )
    await doc.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="college.lms.material.uploaded",
        resource_type="learning_material",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        metadata={"course_code": code, "material_type": material_type},
    )
    return {"material_id": str(doc.id), "course_code": code, "title": label, "material_type": material_type}


async def export_lms_learning_materials_csv(scope: AccessScope) -> str:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    requires_approval = await _publishing_requires_approval(tenant_id)
    docs = await LearningMaterial.find(Eq(LearningMaterial.tenant_id, tenant_id)).sort("-created_at").to_list()
    docs = [d for d in docs if (d.material_type or "document") not in _VIDEO_MATERIAL_TYPES]
    faculty_ids = {str(d.faculty_user_id) for d in docs if d.faculty_user_id}
    faculty_by_id = await _faculty_names(tenant_id, faculty_ids)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Material", "Course", "Type", "Uploaded by", "Date", "Status", "Unit"])
    for doc in docs:
        fid = str(doc.faculty_user_id) if doc.faculty_user_id else ""
        status_label, _ = _material_status(doc, requires_approval=requires_approval)
        writer.writerow(
            [
                doc.title,
                doc.course_code.upper() if doc.course_code else "—",
                _type_label(doc),
                faculty_by_id.get(fid, "—"),
                _date_label(doc.created_at),
                status_label,
                doc.unit_no if doc.unit_no is not None else "—",
            ]
        )
    return buffer.getvalue()


async def export_lms_video_lectures_csv(scope: AccessScope) -> str:
    authorize(scope, Permission.LMS_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    docs = await LearningMaterial.find(Eq(LearningMaterial.tenant_id, tenant_id)).sort("-created_at").to_list()
    videos = [d for d in docs if (d.material_type or "") in _VIDEO_MATERIAL_TYPES]

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Lecture", "Course", "Length", "Uploaded", "Status"])
    for doc in videos:
        status_label, _ = _video_status(doc)
        writer.writerow(
            [
                doc.title,
                doc.course_code.upper() if doc.course_code else "—",
                _duration_label(doc),
                _date_label(doc.created_at),
                status_label,
            ]
        )
    return buffer.getvalue()


async def export_lms_units_chapters_csv(scope: AccessScope, *, course_code: str | None = None) -> str:
    page = await get_lms_unit_chapter_management_page(scope, course_code=course_code)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Course", "Unit", "Unit status", "Chapter", "Materials"])
    course = page.course_header_label
    for unit in page.unit_rows:
        if not unit.chapters:
            writer.writerow([course, unit.unit_label, unit.status_label, "—", "—"])
            continue
        for chapter in unit.chapters:
            writer.writerow(
                [
                    course,
                    unit.unit_label,
                    unit.status_label,
                    chapter.chapter_label,
                    chapter.materials_count_label,
                ]
            )
    return buffer.getvalue()