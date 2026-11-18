"""Finance module hooks for library fines."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.modules.finance.finance_enums import PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction
from app.modules.library.fine_calculation import balance_for_fine
from app.modules.library.fine_enums import LibraryFineRecoveryStatus
from app.modules.library.fine_models import LibraryFineHistory
from app.modules.library.library_enums import LibraryFineStatus
from app.modules.library.library_models import LibraryFine


async def on_demand_paid(tenant_id: PydanticObjectId, demand_id: str | None, transaction_id: str) -> None:
    if not demand_id:
        return
    fine = await LibraryFine.find_one(Eq(LibraryFine.tenant_id, tenant_id), Eq(LibraryFine.demand_id, demand_id))
    if fine is None:
        return
    tx = await PaymentTransaction.find_one(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.transaction_id, transaction_id),
    )
    if tx is None or tx.status != PaymentTransactionStatus.SUCCESS or not tx.webhook_verified:
        return
    if fine.payment_transaction_id == transaction_id and fine.status == LibraryFineStatus.PAID:
        return
    fine.amount_paid = round(fine.amount_paid + tx.amount, 2)
    fine.balance = balance_for_fine(amount=fine.amount, amount_waived=fine.amount_waived, amount_paid=fine.amount_paid)
    fine.payment_transaction_id = transaction_id
    if fine.balance <= 0:
        fine.status = LibraryFineStatus.PAID
        fine.recovery_status = LibraryFineRecoveryStatus.RECOVERED.value
    else:
        fine.status = LibraryFineStatus.OPEN
        fine.recovery_status = LibraryFineRecoveryStatus.PARTIAL.value
    fine.updated_at = utcnow()
    await fine.save()
    await LibraryFineHistory(
        tenant_id=tenant_id,
        fine_id=fine.fine_id,
        action="payment_verified",
        actor_id=None,
        changes={"transaction_id": transaction_id, "amount_paid": tx.amount},
    ).insert()