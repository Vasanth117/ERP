"""Finance vendor registration, verification, and restricted bank details."""

import hashlib
import uuid
from typing import Any

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.phase10_enums import VendorVerificationStatus
from app.modules.accounts_finance.phase10_models import FinanceVendorBankDetail, FinanceVendorVerificationHistory
from app.modules.accounts_finance.policy import (
    authorize_finance_vendor_bank,
    authorize_finance_vendor_manage,
    authorize_finance_vendor_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.finance_ext_models import InstitutionVendorRecord
from app.modules.college_admin.security_admin_service import append_institution_audit


def _mask_account_ref(raw: str) -> str:
    if len(raw) <= 4:
        return "****"
    return f"****{raw[-4:]}"


async def register_vendor(scope: AccessScope, payload: dict[str, Any]) -> dict:
    authorize_finance_vendor_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    vendor_id = payload["vendor_id"].strip()
    vendor_code = (payload.get("vendor_code") or vendor_id).strip().upper()
    dup_code = await InstitutionVendorRecord.find_one(
        Eq(InstitutionVendorRecord.tenant_id, tenant_id),
        Eq(InstitutionVendorRecord.vendor_code, vendor_code),
    )
    if dup_code and dup_code.vendor_id != vendor_id:
        raise AppError(code="CONFLICT", message="Vendor code already in use", status_code=409)
    name = payload["name"].strip()
    gstin = payload.get("gstin")
    if gstin:
        dup_gst = await InstitutionVendorRecord.find_one(
            Eq(InstitutionVendorRecord.tenant_id, tenant_id),
            Eq(InstitutionVendorRecord.gstin, gstin),
        )
        if dup_gst and dup_gst.vendor_id != vendor_id and dup_gst.active:
            raise AppError(code="CONFLICT", message="Duplicate tax identification", status_code=409)
    doc = await InstitutionVendorRecord.find_one(Eq(InstitutionVendorRecord.tenant_id, tenant_id), Eq(InstitutionVendorRecord.vendor_id, vendor_id))
    if doc is None:
        doc = InstitutionVendorRecord(
            tenant_id=tenant_id,
            vendor_id=vendor_id,
            vendor_code=vendor_code,
            name=name,
            category=payload.get("category"),
            gstin=gstin,
            contact_email=payload.get("contact_email"),
            contact_phone=payload.get("contact_phone"),
            address=payload.get("address"),
            authorized_representative=payload.get("authorized_representative"),
            document_refs=payload.get("document_refs") or [],
            verification_status=VendorVerificationStatus.PENDING.value,
        )
        await doc.insert()
    else:
        if doc.verification_status == VendorVerificationStatus.APPROVED.value and payload.get("sensitive_change"):
            doc.verification_status = VendorVerificationStatus.UNDER_REVIEW.value
        doc.name = name
        doc.vendor_code = vendor_code
        doc.category = payload.get("category") or doc.category
        doc.gstin = gstin or doc.gstin
        doc.contact_email = payload.get("contact_email") or doc.contact_email
        doc.contact_phone = payload.get("contact_phone") or doc.contact_phone
        doc.address = payload.get("address") or doc.address
        doc.authorized_representative = payload.get("authorized_representative") or doc.authorized_representative
        doc.document_refs = payload.get("document_refs") or doc.document_refs
        doc.updated_at = utcnow()
        await doc.save()
    if payload.get("bank_account_number"):
        await upsert_vendor_bank(scope, vendor_id, payload)
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.vendor.register",
        module="accounts_finance",
        resource_type="vendor",
        resource_id=vendor_id,
    )
    return {"vendor_id": vendor_id, "vendor_code": vendor_code, "verification_status": doc.verification_status}


async def upsert_vendor_bank(scope: AccessScope, vendor_id: str, payload: dict[str, Any]) -> dict:
    authorize_finance_vendor_bank(scope)
    tenant_id = require_finance_tenant_scope(scope)
    raw = payload["bank_account_number"].strip()
    account_ref = hashlib.sha256(raw.encode()).hexdigest()[:32]
    bank = await FinanceVendorBankDetail.find_one(
        Eq(FinanceVendorBankDetail.tenant_id, tenant_id),
        Eq(FinanceVendorBankDetail.vendor_id, vendor_id),
    )
    if bank is None:
        bank = FinanceVendorBankDetail(
            tenant_id=tenant_id,
            vendor_id=vendor_id,
            bank_name=payload.get("bank_name"),
            account_holder=payload.get("account_holder"),
            account_number_ref=account_ref,
            ifsc=payload.get("ifsc"),
            updated_by=scope.user_id,
        )
        await bank.insert()
    else:
        bank.bank_name = payload.get("bank_name") or bank.bank_name
        bank.account_holder = payload.get("account_holder") or bank.account_holder
        bank.account_number_ref = account_ref
        bank.ifsc = payload.get("ifsc") or bank.ifsc
        bank.updated_by = scope.user_id
        bank.updated_at = utcnow()
        await bank.save()
    return {"vendor_id": vendor_id, "account_number_ref": _mask_account_ref(raw)}


async def verify_vendor(scope: AccessScope, vendor_id: str, *, approved: bool, note: str | None = None) -> dict:
    authorize_finance_vendor_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await InstitutionVendorRecord.find_one(Eq(InstitutionVendorRecord.tenant_id, tenant_id), Eq(InstitutionVendorRecord.vendor_id, vendor_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Vendor not found", status_code=404)
    prev = doc.verification_status
    doc.verification_status = VendorVerificationStatus.APPROVED.value if approved else VendorVerificationStatus.REJECTED.value
    doc.active = approved
    doc.updated_at = utcnow()
    await doc.save()
    await FinanceVendorVerificationHistory(
        tenant_id=tenant_id,
        history_id=f"vfh_{uuid.uuid4().hex[:12]}",
        vendor_id=vendor_id,
        from_status=prev,
        to_status=doc.verification_status,
        actor_id=scope.user_id,
        note=note,
    ).insert()
    return {"vendor_id": vendor_id, "verification_status": doc.verification_status}


async def list_vendors(scope: AccessScope, *, query: str | None = None) -> list[dict]:
    authorize_finance_vendor_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    rows = await InstitutionVendorRecord.find(Eq(InstitutionVendorRecord.tenant_id, tenant_id)).to_list()
    if query:
        q = query.lower()
        rows = [r for r in rows if q in r.name.lower() or q in (r.vendor_code or "").lower()]
    return [
        {
            "vendor_id": r.vendor_id,
            "vendor_code": r.vendor_code,
            "name": r.name,
            "category": r.category,
            "verification_status": r.verification_status,
            "active": r.active,
        }
        for r in rows
    ]


async def get_vendor(scope: AccessScope, vendor_id: str, *, include_bank: bool = False) -> dict:
    authorize_finance_vendor_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await InstitutionVendorRecord.find_one(Eq(InstitutionVendorRecord.tenant_id, tenant_id), Eq(InstitutionVendorRecord.vendor_id, vendor_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Vendor not found", status_code=404)
    out = doc.model_dump()
    out.pop("metadata", None)
    if include_bank:
        authorize_finance_vendor_bank(scope)
        bank = await FinanceVendorBankDetail.find_one(
            Eq(FinanceVendorBankDetail.tenant_id, tenant_id),
            Eq(FinanceVendorBankDetail.vendor_id, vendor_id),
        )
        out["bank"] = None if bank is None else {"bank_name": bank.bank_name, "ifsc": bank.ifsc, "account_mask": "****"}
    else:
        out["bank"] = {"available": False, "reason": "Restricted permission required"}
    return out