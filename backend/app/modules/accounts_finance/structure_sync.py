"""Sync approved/active staff fee structures to authoritative student fee records."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.modules.accounts_finance.models import FinanceFeeStructure, FinanceFeeStructureComponent
from app.modules.college_admin.finance_admin_models import InstitutionFeeStructure
from app.modules.finance.finance_models import StudentFeeStructure


async def sync_active_structure_to_authoritative(
    tenant_id: PydanticObjectId,
    structure: FinanceFeeStructure,
) -> None:
    components = await FinanceFeeStructureComponent.find(
        Eq(FinanceFeeStructureComponent.tenant_id, tenant_id),
        Eq(FinanceFeeStructureComponent.structure_id, structure.structure_id),
    ).to_list()
    line_items = [
        {
            "fee_category_code": c.fee_category_code,
            "component_id": c.component_id,
            "amount": c.amount,
            "due_date": c.due_date.isoformat() if c.due_date else None,
            "billing_frequency": c.billing_frequency.value,
            "mandatory": c.mandatory,
        }
        for c in components
    ]
    programme = structure.programme_code.upper()
    student_ref = await StudentFeeStructure.find_one(
        Eq(StudentFeeStructure.tenant_id, tenant_id),
        Eq(StudentFeeStructure.structure_id, structure.structure_id),
    )
    if student_ref is None:
        student_ref = StudentFeeStructure(
            tenant_id=tenant_id,
            structure_id=structure.structure_id,
            programme_code=programme,
            academic_year_label=structure.academic_year_label,
            semester_label=structure.semester_label,
            line_items=line_items,
            total_amount=structure.total_amount,
            published=True,
        )
        await student_ref.insert()
    else:
        student_ref.programme_code = programme
        student_ref.academic_year_label = structure.academic_year_label
        student_ref.semester_label = structure.semester_label
        student_ref.line_items = line_items
        student_ref.total_amount = structure.total_amount
        student_ref.published = True
        student_ref.updated_at = utcnow()
        await student_ref.save()

    structure.authoritative_student_structure_id = student_ref.id
    await structure.save()

    admin = await InstitutionFeeStructure.find_one(
        Eq(InstitutionFeeStructure.tenant_id, tenant_id),
        Eq(InstitutionFeeStructure.structure_id, structure.structure_id),
    )
    if admin is None:
        admin = InstitutionFeeStructure(
            tenant_id=tenant_id,
            structure_id=structure.structure_id,
            programme_code=programme,
            academic_year_label=structure.academic_year_label,
            semester_label=structure.semester_label,
            line_items=line_items,
            total_amount=structure.total_amount,
            published=True,
            authoritative_structure_id=student_ref.id,
        )
        await admin.insert()
    else:
        admin.line_items = line_items
        admin.total_amount = structure.total_amount
        admin.published = True
        admin.authoritative_structure_id = student_ref.id
        admin.updated_at = utcnow()
        await admin.save()