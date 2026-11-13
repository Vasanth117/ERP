"""Read finance records scoped to a single student."""

from beanie import PydanticObjectId

from app.modules.finance.finance_models import (
    FeeConcession,
    FeeInstallmentSchedule,
    OfficialScholarshipApplication,
    PaymentReceipt,
    PaymentTransaction,
    RefundRecord,
    StudentFeeDemand,
    StudentFeeInvoice,
    StudentFeeStructure,
    StudentFinancialLedgerEntry,
    StudentScholarshipEligibility,
)
from app.modules.students.models import StudentProfile


async def student_programme_code(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> str | None:
    profile = await StudentProfile.find_one({"tenant_id": tenant_id, "user_id": user_id})
    if profile is None:
        return None
    return profile.programme_code


async def fee_structures_for_student(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    *,
    year: str,
    semester: str,
) -> list[StudentFeeStructure]:
    programme = await student_programme_code(tenant_id, user_id)
    filters: dict = {
        "tenant_id": tenant_id,
        "academic_year_label": year,
        "semester_label": semester,
        "published": True,
    }
    if programme:
        filters["programme_code"] = programme
    return await StudentFeeStructure.find(filters).to_list()


async def demands_for_student(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[StudentFeeDemand]:
    return await StudentFeeDemand.find({"tenant_id": tenant_id, "student_user_id": user_id}).sort("-due_date").to_list()


async def invoices_for_student(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[StudentFeeInvoice]:
    return await StudentFeeInvoice.find(
        {"tenant_id": tenant_id, "student_user_id": user_id, "published": True}
    ).sort("-issued_at").to_list()


async def ledger_for_student(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[StudentFinancialLedgerEntry]:
    return await StudentFinancialLedgerEntry.find({"tenant_id": tenant_id, "student_user_id": user_id}).sort(
        "-posted_at"
    ).to_list()


async def payments_for_student(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[PaymentTransaction]:
    return await PaymentTransaction.find({"tenant_id": tenant_id, "student_user_id": user_id}).sort("-created_at").to_list()


async def receipts_for_student(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[PaymentReceipt]:
    return await PaymentReceipt.find({"tenant_id": tenant_id, "student_user_id": user_id}).sort("-issued_at").to_list()


async def installment_schedules(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[FeeInstallmentSchedule]:
    return await FeeInstallmentSchedule.find(
        {"tenant_id": tenant_id, "student_user_id": user_id, "published": True}
    ).to_list()


async def scholarship_eligibility_rows(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId
) -> list[StudentScholarshipEligibility]:
    return await StudentScholarshipEligibility.find(
        {"tenant_id": tenant_id, "student_user_id": user_id, "published": True}
    ).to_list()


async def official_scholarship_application(
    tenant_id: PydanticObjectId, user_id: PydanticObjectId, application_id: str
) -> OfficialScholarshipApplication | None:
    return await OfficialScholarshipApplication.find_one(
        {"tenant_id": tenant_id, "student_user_id": user_id, "application_id": application_id}
    )


async def concessions_for_student(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[FeeConcession]:
    return await FeeConcession.find(
        {"tenant_id": tenant_id, "student_user_id": user_id, "published": True}
    ).to_list()


async def refunds_for_student(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[RefundRecord]:
    return await RefundRecord.find({"tenant_id": tenant_id, "student_user_id": user_id}).sort("-created_at").to_list()
