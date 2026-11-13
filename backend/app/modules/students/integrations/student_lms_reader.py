"""Read published LMS materials for enrolled students."""

from beanie import PydanticObjectId

from app.modules.lms.enums import MaterialPublishState
from app.modules.lms.models import LearningMaterial
from app.modules.students.integrations.data_reader import StudentDataReader

_reader = StudentDataReader()


async def enrolled_course_pairs(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> set[tuple[str, str | None]]:
    roster = await _reader.roster_entries(tenant_id, user_id, academic_year_label=year, semester_label=semester)
    return {(r.course_code, r.section_code) for r in roster}


async def published_materials_for_student(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
    course_code: str | None = None,
    subject_id: str | None = None,
    unit_no: int | None = None,
    material_type: str | None = None,
) -> list[LearningMaterial]:
    pairs = await enrolled_course_pairs(tenant_id, user_id, year=year, semester=semester)
    if not pairs:
        return []
    codes = {p[0] for p in pairs}
    if course_code is not None:
        if course_code not in codes:
            return []
        codes = {course_code}
    filters: dict = {
        "tenant_id": tenant_id,
        "course_code": {"$in": list(codes)},
        "publish_state": MaterialPublishState.PUBLISHED,
    }
    if subject_id:
        filters["subject_id"] = subject_id
    if unit_no is not None:
        filters["unit_no"] = unit_no
    if material_type:
        filters["material_type"] = material_type
    docs = await LearningMaterial.find(filters).sort([("course_code", 1), ("unit_no", 1), ("title", 1)]).to_list()
    sections_by_course = {c: s for c, s in pairs}
    allowed: list[LearningMaterial] = []
    for doc in docs:
        section = sections_by_course.get(doc.course_code)
        if doc.section is not None and doc.section != section:
            continue
        allowed.append(doc)
    return allowed


async def authorized_material(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    material_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> LearningMaterial | None:
    doc = await LearningMaterial.get(material_id)
    if doc is None or doc.tenant_id != tenant_id or doc.publish_state != MaterialPublishState.PUBLISHED:
        return None
    pairs = await enrolled_course_pairs(tenant_id, user_id, year=year, semester=semester)
    course_sections = {c: s for c, s in pairs}
    if doc.course_code not in course_sections:
        return None
    section = course_sections[doc.course_code]
    if doc.section is not None and doc.section != section:
        return None
    return doc
