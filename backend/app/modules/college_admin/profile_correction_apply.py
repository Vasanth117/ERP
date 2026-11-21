"""Apply approved student profile correction requests."""

from __future__ import annotations

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.student_admin_models import StudentAdmission, StudentGuardianRelationship, StudentRecord
from app.modules.students.models import StudentProfile
from app.modules.students.profile_correction_fields import GUARDIAN_CORRECTION_ATTR, METADATA_FIELD_KEYS
from app.modules.students.student_portal_models import StudentProfileCorrectionRequest


def _relationship_matches(relationship: str, token: str) -> bool:
    r = relationship.strip().lower()
    t = token.strip().lower()
    return t in r or r.startswith(t)


async def apply_profile_correction(
    tenant_id: PydanticObjectId,
    row: StudentProfileCorrectionRequest,
) -> None:
    field = row.field_name
    value = row.proposed_value.strip()
    if not value:
        return

    profile = await StudentProfile.find_one(
        Eq(StudentProfile.tenant_id, tenant_id),
        Eq(StudentProfile.user_id, row.user_id),
    )
    record = await StudentRecord.find_one(
        Eq(StudentRecord.tenant_id, tenant_id),
        Eq(StudentRecord.user_id, row.user_id),
    )
    admission = None
    if profile and profile.admission_number:
        admission = await StudentAdmission.find_one(
            Eq(StudentAdmission.tenant_id, tenant_id),
            Eq(StudentAdmission.admission_number, profile.admission_number),
        )

    if field == "display_name":
        user = await User.get(row.user_id)
        if user:
            user.full_name = value
            await user.save()
        if admission:
            admission.applicant_name = value
            admission.updated_at = utcnow()
            await admission.save()
        return

    if field in METADATA_FIELD_KEYS:
        if admission is None and profile and profile.admission_number:
            admission = await StudentAdmission.find_one(
                Eq(StudentAdmission.tenant_id, tenant_id),
                Eq(StudentAdmission.admission_number, profile.admission_number),
            )
        if admission is None:
            return
        meta = dict(admission.metadata or {})
        primary = METADATA_FIELD_KEYS[field][0]
        meta[primary] = value
        admission.metadata = meta
        admission.updated_at = utcnow()
        await admission.save()
        if field == "batch_label" and profile:
            profile.batch_label = value
            profile.updated_at = utcnow()
            await profile.save()
        return

    if field in GUARDIAN_CORRECTION_ATTR:
        rel_token, attr = GUARDIAN_CORRECTION_ATTR[field]
        guardians = await StudentGuardianRelationship.find(
            Eq(StudentGuardianRelationship.tenant_id, tenant_id),
            Eq(StudentGuardianRelationship.user_id, row.user_id),
        ).to_list()
        target = next((g for g in guardians if _relationship_matches(g.relationship, rel_token)), None)
        if target is None:
            return
        if attr == "guardian_name":
            target.guardian_name = value
        elif attr == "phone":
            target.phone = value
        elif attr == "email":
            target.email = value.lower() if value else None
        elif attr == "occupation":
            target.occupation = value
        target.updated_at = utcnow()
        await target.save()
        return

    if profile is None:
        return

    if field == "roll_number":
        profile.roll_number = value
        if record:
            record.roll_number = value
    elif field == "admission_number":
        profile.admission_number = value
        if record:
            record.admission_number = value
        if admission:
            admission.admission_number = value
            admission.updated_at = utcnow()
            await admission.save()
    elif field == "programme_name":
        profile.programme_name = value
        if admission:
            meta = dict(admission.metadata or {})
            meta["programme_name"] = value
            admission.metadata = meta
            admission.updated_at = utcnow()
            await admission.save()
    elif field == "programme_code":
        profile.programme_code = value
        if record:
            record.programme_code = value
    elif field == "section_code":
        profile.section_code = value
        if record:
            record.section_code = value
    elif field == "batch_label":
        profile.batch_label = value
        if record:
            record.batch_label = value
        if admission:
            admission.batch_label = value
            admission.updated_at = utcnow()
            await admission.save()

    profile.updated_at = utcnow()
    await profile.save()
    if record:
        record.updated_at = utcnow()
        await record.save()