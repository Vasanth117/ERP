"""Examination cell — transcripts and academic document generation."""

import hashlib
import hmac
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.models import InstitutionProfile
from app.modules.examinations.exam_cell_document_pdf import build_result_document_pdf
from app.modules.examinations.exam_cell_grading_enums import ExamSubjectResultStatus
from app.modules.examinations.exam_cell_grading_models import ExamSemesterResult, ExamStudentSubjectResult
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_document_generate,
    require_examination_cell_tenant,
)
from app.modules.examinations.exam_cell_publication_enums import ExamPublicationStatus, ExamResultDocumentType
from app.modules.examinations.exam_cell_publication_models import (
    ExamAcademicStatement,
    ExamDocumentVerificationRecord,
    ExamResultDocument,
    ExamResultPublication,
    ExamStudentResultVisibility,
    ExamTranscript,
)
from app.modules.examinations.exam_cell_publication_schemas import (
    ExamDocumentBulkGenerateRequest,
    ExamDocumentGenerateRequest,
    ExamDocumentRead,
    ExamDocumentVerifyRequest,
    ExamDocumentVerifyResponse,
)
from app.modules.examinations.exam_cell_publication_service import _student_may_view_publication
from app.modules.lms.storage import read_bytes, storage_key_for, write_bytes
from app.modules.students.models import StudentProfile
from app.modules.students.policy import require_student_scope


def _document_id() -> str:
    return f"erd_{uuid4().hex[:10]}"


def _verification_code(document_id: str, student_id: PydanticObjectId, version: int) -> str:
    secret = get_settings().jwt_secret.encode()
    digest = hmac.new(secret, f"{document_id}:{student_id}:{version}".encode(), hashlib.sha256).hexdigest()
    return digest[:16].upper()


async def _assert_published_access(
    tenant_id: PydanticObjectId,
    publication: ExamResultPublication,
    student_oid: PydanticObjectId,
) -> None:
    if publication.status != ExamPublicationStatus.PUBLISHED:
        raise AppError(code="FORBIDDEN", message="Documents require a published result set", status_code=403)
    vis = await ExamStudentResultVisibility.find_one(
        Eq(ExamStudentResultVisibility.tenant_id, tenant_id),
        Eq(ExamStudentResultVisibility.publication_id, publication.publication_id),
        Eq(ExamStudentResultVisibility.student_user_id, student_oid),
    )
    if not _student_may_view_publication(publication, vis):
        raise AppError(code="FORBIDDEN", message="Student result is not visible", status_code=403)


async def _institution_name(tenant_id: PydanticObjectId) -> str:
    profile = await InstitutionProfile.find_one(Eq(InstitutionProfile.tenant_id, tenant_id))
    return profile.name if profile and profile.name else "Institution"


def _document_title(document_type: ExamResultDocumentType) -> str:
    titles = {
        ExamResultDocumentType.GRADE_CARD: "Semester Grade Card",
        ExamResultDocumentType.MARKSHEET: "Consolidated Marksheet",
        ExamResultDocumentType.TRANSCRIPT: "Academic Transcript",
        ExamResultDocumentType.ACADEMIC_STATEMENT: "Academic Statement",
        ExamResultDocumentType.PROVISIONAL_STATEMENT: "Provisional Academic Statement",
    }
    return titles.get(document_type, "Examination Document")


async def generate_document(scope: AccessScope, actor: User, payload: ExamDocumentGenerateRequest) -> ExamDocumentRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_document_generate(scope)

    publication = await ExamResultPublication.find_one(
        Eq(ExamResultPublication.tenant_id, tenant_id),
        Eq(ExamResultPublication.publication_id, payload.publication_id),
    )
    if publication is None:
        raise AppError(code="NOT_FOUND", message="Publication not found", status_code=404)

    student_oid = to_object_id(payload.student_user_id, "student_user_id")
    await _assert_published_access(tenant_id, publication, student_oid)

    profile = await StudentProfile.find_one(
        Eq(StudentProfile.tenant_id, tenant_id),
        Eq(StudentProfile.user_id, student_oid),
    )
    subjects = await ExamStudentSubjectResult.find(
        Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
        Eq(ExamStudentSubjectResult.exam_session_id, publication.exam_session_id),
        Eq(ExamStudentSubjectResult.student_user_id, student_oid),
        Eq(ExamStudentSubjectResult.status, ExamSubjectResultStatus.APPROVED),
    ).to_list()
    if payload.course_code:
        subjects = [s for s in subjects if s.course_code == payload.course_code.strip().upper()]
    if not subjects:
        raise AppError(code="NOT_FOUND", message="No approved subject results for document", status_code=404)

    sem = await ExamSemesterResult.find_one(
        Eq(ExamSemesterResult.tenant_id, tenant_id),
        Eq(ExamSemesterResult.exam_session_id, publication.exam_session_id),
        Eq(ExamSemesterResult.student_user_id, student_oid),
    )

    lines = [
        f"Institution: {await _institution_name(tenant_id)}",
        f"Student roll: {profile.roll_number if profile else 'N/A'}",
        f"Publication: {publication.publication_id} v{publication.version}",
        f"Policy: {publication.policy_id} v{publication.policy_version}",
    ]
    if sem:
        lines.append(f"GPA: {sem.gpa}  CGPA: {sem.cgpa}")
    for sub in subjects:
        lines.append(
            f"{sub.course_code}: {sub.grade_letter} ({sub.grade_point} pts) credits {sub.credits_earned}/{sub.credit_units}"
        )

    doc_id = _document_id()
    verification = _verification_code(doc_id, student_oid, publication.version)
    pdf = build_result_document_pdf(title=_document_title(payload.document_type), lines=lines)
    file_name = f"{payload.document_type.value}_{student_oid}.pdf"
    key = storage_key_for(str(tenant_id), "exam_result_documents", file_name)
    storage_key, checksum = write_bytes(key, pdf)

    doc = ExamResultDocument(
        tenant_id=tenant_id,
        document_id=doc_id,
        document_type=payload.document_type,
        publication_id=publication.publication_id,
        exam_session_id=publication.exam_session_id,
        student_user_id=student_oid,
        version=publication.version,
        storage_key=storage_key,
        checksum=checksum,
        verification_code=verification,
        file_name=file_name,
        generated_by=actor.id,
    )
    await doc.insert()

    if payload.document_type == ExamResultDocumentType.TRANSCRIPT:
        await ExamTranscript(
            tenant_id=tenant_id,
            transcript_id=f"etr_{uuid4().hex[:10]}",
            student_user_id=student_oid,
            publication_id=publication.publication_id,
            document_id=doc_id,
            programme_code=profile.programme_code if profile else None,
            cgpa=sem.cgpa if sem else None,
            includes_arrear=payload.include_arrear,
        ).insert()
    elif payload.document_type in {
        ExamResultDocumentType.ACADEMIC_STATEMENT,
        ExamResultDocumentType.PROVISIONAL_STATEMENT,
    }:
        course = subjects[0].course_code
        await ExamAcademicStatement(
            tenant_id=tenant_id,
            statement_id=f"eas_{uuid4().hex[:10]}",
            student_user_id=student_oid,
            publication_id=publication.publication_id,
            document_id=doc_id,
            course_code=course,
            exam_session_id=publication.exam_session_id,
            is_provisional=payload.document_type == ExamResultDocumentType.PROVISIONAL_STATEMENT,
        ).insert()

    return ExamDocumentRead.from_doc(doc)


async def bulk_generate_documents(scope: AccessScope, actor: User, payload: ExamDocumentBulkGenerateRequest) -> list[ExamDocumentRead]:
    tenant_id = require_examination_cell_tenant(scope)
    publication = await ExamResultPublication.find_one(
        Eq(ExamResultPublication.tenant_id, tenant_id),
        Eq(ExamResultPublication.publication_id, payload.publication_id),
    )
    if publication is None:
        raise AppError(code="NOT_FOUND", message="Publication not found", status_code=404)

    ids = payload.student_user_ids or publication.dataset_snapshot.get("student_user_ids") or []
    results: list[ExamDocumentRead] = []
    for sid in ids:
        results.append(
            await generate_document(
                scope,
                actor,
                ExamDocumentGenerateRequest(
                    publication_id=payload.publication_id,
                    student_user_id=sid,
                    document_type=payload.document_type,
                ),
            )
        )
    return results


async def download_document(scope: AccessScope, actor: User, document_id: str) -> tuple[bytes, str]:
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamResultDocument.find_one(
        Eq(ExamResultDocument.tenant_id, tenant_id),
        Eq(ExamResultDocument.document_id, document_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Document not found", status_code=404)

    publication = await ExamResultPublication.find_one(
        Eq(ExamResultPublication.tenant_id, tenant_id),
        Eq(ExamResultPublication.publication_id, doc.publication_id),
    )
    if publication is None:
        raise AppError(code="NOT_FOUND", message="Publication not found", status_code=404)

    is_staff = (
        Permission.EXAMINATION_CELL_DOCUMENT_GENERATE in scope.effective_permissions
        or Permission.EXAMINATION_CELL_PUBLICATION_PUBLISH in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_PUBLISH in scope.effective_permissions
    )
    if not is_staff:
        if Permission.STUDENT_EXAM_RESULTS_READ in scope.effective_permissions:
            require_student_scope(scope)
            if scope.user_id != doc.student_user_id:
                raise AppError(code="FORBIDDEN", message="Cannot access another student's document", status_code=403)
        else:
            raise AppError(code="FORBIDDEN", message="Not authorized to download document", status_code=403)
        await _assert_published_access(tenant_id, publication, doc.student_user_id)
    else:
        authorize_examination_cell_document_generate(scope)

    data = read_bytes(doc.storage_key)
    return data, doc.file_name


async def verify_document(scope: AccessScope, payload: ExamDocumentVerifyRequest) -> ExamDocumentVerifyResponse:
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamResultDocument.find_one(
        Eq(ExamResultDocument.tenant_id, tenant_id),
        Eq(ExamResultDocument.document_id, payload.document_id),
    )
    if doc is None:
        return ExamDocumentVerifyResponse(valid=False, document_id=payload.document_id, document_type=None, student_user_id=None)

    expected = _verification_code(doc.document_id, doc.student_user_id, doc.version)
    valid = hmac.compare_digest(expected, payload.verification_code.strip().upper())

    await ExamDocumentVerificationRecord(
        tenant_id=tenant_id,
        record_id=f"evr_{uuid4().hex[:10]}",
        document_id=doc.document_id,
        verification_code=payload.verification_code.strip().upper(),
        verified=valid,
        actor_id=scope.user_id,
    ).insert()

    return ExamDocumentVerifyResponse(
        valid=valid,
        document_id=doc.document_id,
        document_type=doc.document_type if valid else None,
        student_user_id=str(doc.student_user_id) if valid else None,
    )