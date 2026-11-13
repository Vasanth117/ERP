"""Library administration API schemas."""

from pydantic import BaseModel, Field

from app.modules.library.library_enums import LibraryFineStatus


class LibraryBranchCreate(BaseModel):
    branch_code: str
    name: str
    campus_id: str | None = None
    address: str | None = None


class CatalogueCreate(BaseModel):
    book_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    isbn: str | None = None
    category: str | None = None
    branch_code: str | None = None


class BookCopyCreate(BaseModel):
    copy_id: str
    book_id: str
    barcode: str
    accession_number: str | None = None
    branch_code: str | None = None


class BorrowingPolicyUpsert(BaseModel):
    branch_code: str | None = None
    max_books: int = Field(default=5, ge=0)
    loan_days: int = Field(default=14, ge=1)
    renewal_limit: int = 2
    fine_per_day: float = Field(default=5.0, ge=0)


class CirculationIssue(BaseModel):
    student_user_id: str
    copy_id: str
    branch_code: str | None = None


class CirculationReturn(BaseModel):
    circulation_id: str


class ReservationFulfill(BaseModel):
    reservation_id: str


class FineDecision(BaseModel):
    fine_id: str
    decision: LibraryFineStatus
    note: str | None = None


class AcquisitionCreate(BaseModel):
    acquisition_id: str
    book_id: str | None = None
    branch_code: str | None = None
    vendor: str | None = None
    quantity: int = Field(default=1, ge=1)
