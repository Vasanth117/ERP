"""Phase 3 payment enumerations."""

from enum import Enum


class PaymentGatewayEnvironment(str, Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class OnlinePaymentMethod(str, Enum):
    UPI = "upi"
    DEBIT_CARD = "debit_card"
    CREDIT_CARD = "credit_card"
    NET_BANKING = "net_banking"
    OTHER = "other"


class OfflinePaymentMethod(str, Enum):
    CASH = "cash"
    CHEQUE = "cheque"
    DEMAND_DRAFT = "demand_draft"
    BANK_TRANSFER = "bank_transfer"
    NEFT = "neft"
    RTGS = "rtgs"
    IMPS = "imps"
    OTHER = "other"


class OfflinePaymentStatus(str, Enum):
    RECORDED = "recorded"
    AWAITING_VERIFICATION = "awaiting_verification"
    VERIFIED = "verified"
    POSTED = "posted"
    CHEQUE_PENDING = "cheque_pending"
    CHEQUE_CLEARED = "cheque_cleared"
    CHEQUE_BOUNCED = "cheque_bounced"
    REJECTED = "rejected"
    REVERSED = "reversed"
    RECONCILED = "reconciled"