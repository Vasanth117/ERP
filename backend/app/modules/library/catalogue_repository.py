"""Catalogue data access and search."""

from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.modules.library.catalogue_enums import CatalogueSortField, CatalogueSortOrder
from app.modules.library.library_models import LibraryCatalogHistory, LibraryCatalogItem


def _sort_field(sort_by: CatalogueSortField) -> str:
    mapping = {
        CatalogueSortField.TITLE: "title",
        CatalogueSortField.UPDATED_AT: "updated_at",
        CatalogueSortField.CREATED_AT: "created_at",
        CatalogueSortField.PUBLICATION_YEAR: "publication_year",
    }
    return mapping[sort_by]


class CatalogueRepository:
    async def get_by_book_id(self, tenant_id: PydanticObjectId, book_id: str) -> LibraryCatalogItem | None:
        return await LibraryCatalogItem.find_one(
            Eq(LibraryCatalogItem.tenant_id, tenant_id),
            Eq(LibraryCatalogItem.book_id, book_id.strip()),
        )

    async def find_by_isbn(self, tenant_id: PydanticObjectId, *, isbn: str | None, isbn13: str | None) -> LibraryCatalogItem | None:
        if isbn:
            row = await LibraryCatalogItem.find_one(
                Eq(LibraryCatalogItem.tenant_id, tenant_id),
                Eq(LibraryCatalogItem.isbn, isbn),
            )
            if row:
                return row
        if isbn13:
            return await LibraryCatalogItem.find_one(
                Eq(LibraryCatalogItem.tenant_id, tenant_id),
                Eq(LibraryCatalogItem.isbn13, isbn13),
            )
        return None

    async def search(
        self,
        tenant_id: PydanticObjectId,
        *,
        q: str | None,
        category: str | None,
        subcategory: str | None,
        language: str | None,
        primary_library_code: str | None,
        include_archived: bool,
        sort_by: CatalogueSortField,
        sort_order: CatalogueSortOrder,
        limit: int,
        offset: int,
    ) -> tuple[list[LibraryCatalogItem], int]:
        match: dict[str, Any] = {"tenant_id": tenant_id}
        if not include_archived:
            match["archived"] = False
        if category:
            match["category"] = category.strip()
        if subcategory:
            match["subcategory"] = subcategory.strip()
        if language:
            match["language"] = language.strip()
        if primary_library_code:
            match["primary_library_code"] = primary_library_code.strip().upper()
        if q:
            term = q.strip()
            match["$or"] = [
                {"title": {"$regex": term, "$options": "i"}},
                {"subtitle": {"$regex": term, "$options": "i"}},
                {"authors": {"$regex": term, "$options": "i"}},
                {"isbn": term},
                {"isbn13": term},
                {"publisher": {"$regex": term, "$options": "i"}},
                {"keywords": term},
                {"tags": term},
            ]
        direction = "-" if sort_order == CatalogueSortOrder.DESC else "+"
        query = LibraryCatalogItem.find(match).sort(f"{direction}{_sort_field(sort_by)}")
        total = await query.count()
        rows = await query.skip(offset).limit(limit).to_list()
        return rows, total

    async def append_history(
        self,
        tenant_id: PydanticObjectId,
        *,
        book_id: str,
        action: str,
        actor_id: PydanticObjectId | None,
        snapshot: dict[str, Any],
    ) -> None:
        await LibraryCatalogHistory(
            tenant_id=tenant_id,
            book_id=book_id,
            action=action,
            actor_id=actor_id,
            snapshot=snapshot,
        ).insert()

    async def list_history(
        self,
        tenant_id: PydanticObjectId,
        book_id: str,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[LibraryCatalogHistory], int]:
        query = LibraryCatalogHistory.find(
            Eq(LibraryCatalogHistory.tenant_id, tenant_id),
            Eq(LibraryCatalogHistory.book_id, book_id),
        ).sort("-created_at")
        total = await query.count()
        rows = await query.skip(offset).limit(limit).to_list()
        return rows, total