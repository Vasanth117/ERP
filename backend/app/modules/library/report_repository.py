"""MongoDB aggregation pipelines for library reports."""

from __future__ import annotations

from datetime import date

from app.modules.college_admin.library_admin_models import LibraryAcquisition, LibraryMembershipReference
from app.modules.library.dashboard_repository import LibraryDashboardRepository
from app.modules.library.dashboard_filters import build_dashboard_context
from app.modules.library.digital_models import LibraryDigitalAccessLog
from app.modules.library.fine_models import LibraryDamageReport
from app.modules.library.library_enums import (
    LibraryCirculationStatus,
    LibraryCopyStatus,
    LibraryDashboardDateRange,
    LibraryFineStatus,
    LibraryReservationStatus,
)
from app.modules.library.library_models import (
    LibraryCatalogItem,
    LibraryCirculation,
    LibraryCopy,
    LibraryDigitalResource,
    LibraryFine,
    LibraryReservation,
)
from app.modules.library.report_filters import LibraryReportContext, circulation_match, copy_match
from app.modules.library.report_enums import LibraryReportType


class LibraryReportRepository:
    def __init__(self) -> None:
        self._dashboard = LibraryDashboardRepository()

    async def build(self, ctx: LibraryReportContext, report_type: str) -> tuple[list[dict], dict]:
        builders = {
            LibraryReportType.OVERVIEW.value: self._overview,
            LibraryReportType.CATALOGUE.value: self._catalogue,
            LibraryReportType.INVENTORY.value: self._inventory,
            LibraryReportType.CIRCULATION.value: self._circulation_summary,
            LibraryReportType.OVERDUE.value: self._overdue_books,
            LibraryReportType.MEMBER_ACTIVITY.value: self._member_activity,
            LibraryReportType.CIRCULATION_HISTORY.value: self._circulation_history,
            LibraryReportType.RESERVATIONS.value: self._reservations,
            LibraryReportType.FINES.value: self._fines,
            LibraryReportType.LOST_DAMAGED.value: self._lost_damaged,
            LibraryReportType.ACQUISITION.value: self._acquisition,
            LibraryReportType.DIGITAL_USAGE.value: self._digital_usage,
            LibraryReportType.BRANCH_PERFORMANCE.value: self._branch_performance,
            LibraryReportType.POPULAR_BOOKS.value: self._popular_books,
        }
        fn = builders.get(report_type)
        if fn is None:
            return [], {}
        return await fn(ctx)

    async def _overview(self, ctx: LibraryReportContext) -> tuple[list[dict], dict]:
        dash = await build_dashboard_context(
            ctx.tenant_id,
            branch_code=ctx.branch_code,
            category=ctx.category,
            copy_status=None,
            anchor_date=ctx.date_to,
            date_range=LibraryDashboardDateRange.MONTH,
        )
        catalogue = await self._dashboard.catalogue_stats(dash)
        copies = await self._dashboard.copy_inventory(dash)
        members = await self._dashboard.member_stats(dash)
        fines = await self._dashboard.outstanding_fines(dash)
        acquisitions = await self._dashboard.acquisition_summary(dash)
        digital = await self._dashboard.digital_stats(dash)
        totals = {
            "catalogue_titles": catalogue.total_titles,
            "total_copies": copies.total_copies,
            "available_copies": copies.available,
            "issued_copies": copies.issued,
            "overdue_loans": copies.overdue_loans,
            "members_total": members.total,
            "members_active": members.active,
            "open_fines_count": fines.open_count,
            "open_fines_amount": fines.total_amount,
            "pending_acquisitions": acquisitions.pending_procurement_count,
            "digital_resources": digital.total,
            "digital_published": digital.published,
        }
        return [totals], totals

    async def _catalogue(self, ctx: LibraryReportContext) -> tuple[list[dict], dict]:
        match: dict = {"tenant_id": ctx.tenant_id, "archived": False}
        if ctx.category:
            match["category"] = ctx.category
        if ctx.scoped_book_ids is not None:
            match["book_id"] = {"$in": list(ctx.scoped_book_ids)}
        pipeline = [
            {"$match": match},
            {"$group": {"_id": {"category": "$category", "year": "$publication_year"}, "titles": {"$sum": 1}}},
            {"$sort": {"titles": -1}},
        ]
        rows: list[dict] = []
        collection = LibraryCatalogItem.get_motor_collection()
        async for row in collection.aggregate(pipeline):
            key = row["_id"]
            rows.append(
                {
                    "category": key.get("category") or "uncategorized",
                    "publication_year": key.get("year"),
                    "title_count": row["titles"],
                }
            )
        return rows, {"title_groups": len(rows), "total_titles": sum(r["title_count"] for r in rows)}

    async def _inventory(self, ctx: LibraryReportContext) -> tuple[list[dict], dict]:
        match = copy_match(ctx)
        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        rows: list[dict] = []
        collection = LibraryCopy.get_motor_collection()
        async for row in collection.aggregate(pipeline):
            rows.append({"status": row["_id"], "copy_count": row["count"]})
        return rows, {"total_copies": sum(r["copy_count"] for r in rows)}

    async def _circulation_summary(self, ctx: LibraryReportContext) -> tuple[list[dict], dict]:
        base = circulation_match(ctx)
        issued = await LibraryCirculation.find({**base, "issued_at": {"$gte": ctx.window_start, "$lt": ctx.window_end}}).count()
        returned = await LibraryCirculation.find({**base, "returned_at": {"$gte": ctx.window_start, "$lt": ctx.window_end}}).count()
        active = await LibraryCirculation.find(
            {**base, "status": {"$in": [LibraryCirculationStatus.ACTIVE.value, LibraryCirculationStatus.OVERDUE.value]}}
        ).count()
        available = await LibraryCopy.find({**copy_match(ctx), "status": LibraryCopyStatus.AVAILABLE.value}).count()
        row = {
            "period_from": ctx.date_from.isoformat(),
            "period_to": ctx.date_to.isoformat(),
            "issues_in_period": issued,
            "returns_in_period": returned,
            "active_loans": active,
            "available_copies": available,
        }
        return [row], row

    async def _overdue_books(self, ctx: LibraryReportContext) -> tuple[list[dict], dict]:
        today = date.today()
        match = {
            **circulation_match(ctx),
            "status": {"$in": [LibraryCirculationStatus.ACTIVE.value, LibraryCirculationStatus.OVERDUE.value]},
            "due_at": {"$lt": today},
        }
        rows = await LibraryCirculation.find(match).sort("due_at").limit(5000).to_list()
        data = [
            {
                "circulation_id": r.circulation_id,
                "book_id": r.book_id,
                "title": r.title,
                "copy_id": r.copy_id,
                "due_at": r.due_at.isoformat(),
                "student_user_id": str(r.student_user_id),
                "branch_code": r.branch_code,
            }
            for r in rows
        ]
        return data, {"overdue_count": len(data)}

    async def _member_activity(self, ctx: LibraryReportContext) -> tuple[list[dict], dict]:
        match = {**circulation_match(ctx), "issued_at": {"$gte": ctx.window_start, "$lt": ctx.window_end}}
        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$student_user_id", "issues": {"$sum": 1}}},
            {"$sort": {"issues": -1}},
            {"$limit": 2000},
        ]
        rows: list[dict] = []
        collection = LibraryCirculation.get_motor_collection()
        async for row in collection.aggregate(pipeline):
            uid = row["_id"]
            if ctx.member_category:
                mem = await LibraryMembershipReference.find_one(
                    {"tenant_id": ctx.tenant_id, "member_user_id": uid, "member_category": ctx.member_category}
                )
                if mem is None:
                    continue
            rows.append({"member_user_id": str(uid), "issues_in_period": row["issues"]})
        return rows, {"active_members": len(rows)}

    async def _circulation_history(self, ctx: LibraryReportContext) -> tuple[list[dict], dict]:
        match = {
            **circulation_match(ctx),
            "$or": [
                {"issued_at": {"$gte": ctx.window_start, "$lt": ctx.window_end}},
                {"returned_at": {"$gte": ctx.window_start, "$lt": ctx.window_end}},
            ],
        }
        rows = await LibraryCirculation.find(match).sort("-issued_at").limit(5000).to_list()
        data = [
            {
                "circulation_id": r.circulation_id,
                "title": r.title,
                "status": r.status.value,
                "issued_at": r.issued_at.isoformat(),
                "returned_at": r.returned_at.isoformat() if r.returned_at else None,
                "due_at": r.due_at.isoformat(),
            }
            for r in rows
        ]
        return data, {"events": len(data)}

    async def _reservations(self, ctx: LibraryReportContext) -> tuple[list[dict], dict]:
        match: dict = {"tenant_id": ctx.tenant_id}
        if ctx.branch_code:
            match["branch_code"] = ctx.branch_code
        if ctx.scoped_book_ids is not None:
            match["book_id"] = {"$in": list(ctx.scoped_book_ids)}
        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        rows: list[dict] = []
        collection = LibraryReservation.get_motor_collection()
        async for row in collection.aggregate(pipeline):
            rows.append({"status": row["_id"], "count": row["count"]})
        fulfilled = sum(r["count"] for r in rows if r["status"] == LibraryReservationStatus.FULFILLED.value)
        total = sum(r["count"] for r in rows)
        fill_rate = round(fulfilled / total, 4) if total else 0.0
        return rows, {"total_reservations": total, "fill_rate": fill_rate}

    async def _fines(self, ctx: LibraryReportContext) -> tuple[list[dict], dict]:
        match: dict = {"tenant_id": ctx.tenant_id}
        if ctx.branch_code:
            match["branch_code"] = ctx.branch_code
        match["created_at"] = {"$gte": ctx.window_start, "$lt": ctx.window_end}
        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "amount": {"$sum": "$amount"},
                    "balance": {"$sum": "$balance"},
                }
            },
        ]
        rows: list[dict] = []
        collection = LibraryFine.get_motor_collection()
        async for row in collection.aggregate(pipeline):
            rows.append(
                {
                    "status": row["_id"],
                    "fine_count": row["count"],
                    "total_amount": round(float(row["amount"]), 2),
                    "outstanding_balance": round(float(row["balance"]), 2),
                }
            )
        open_match = {**match, "status": LibraryFineStatus.OPEN.value}
        open_count = await LibraryFine.find(open_match).count()
        return rows, {"open_fines_in_scope": open_count}

    async def _lost_damaged(self, ctx: LibraryReportContext) -> tuple[list[dict], dict]:
        match = {
            **copy_match(ctx),
            "status": {"$in": [LibraryCopyStatus.LOST.value, LibraryCopyStatus.DAMAGED.value]},
        }
        copies = await LibraryCopy.find(match).limit(5000).to_list()
        copy_rows = [
            {"copy_id": c.copy_id, "book_id": c.book_id, "status": c.status.value, "branch_code": c.branch_code} for c in copies
        ]
        dmg_match: dict = {"tenant_id": ctx.tenant_id, "created_at": {"$gte": ctx.window_start, "$lt": ctx.window_end}}
        if ctx.branch_code:
            dmg_match["branch_code"] = ctx.branch_code
        reports = await LibraryDamageReport.find(dmg_match).limit(2000).to_list()
        dmg_rows = [{"report_id": r.report_id, "fine_id": r.fine_id, "report_type": r.report_type, "amount": r.replacement_cost} for r in reports]
        return copy_rows + dmg_rows, {"lost_damaged_copies": len(copy_rows), "damage_reports": len(dmg_rows)}

    async def _acquisition(self, ctx: LibraryReportContext) -> tuple[list[dict], dict]:
        match: dict = {
            "tenant_id": ctx.tenant_id,
            "created_at": {"$gte": ctx.window_start, "$lt": ctx.window_end},
        }
        if ctx.branch_code:
            match["branch_code"] = ctx.branch_code
        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        rows: list[dict] = []
        collection = LibraryAcquisition.get_motor_collection()
        async for row in collection.aggregate(pipeline):
            rows.append({"status": row["_id"], "request_count": row["count"]})
        return rows, {"total_requests": sum(r["request_count"] for r in rows)}

    async def _digital_usage(self, ctx: LibraryReportContext) -> tuple[list[dict], dict]:
        match: dict = {
            "tenant_id": ctx.tenant_id,
            "created_at": {"$gte": ctx.window_start, "$lt": ctx.window_end},
        }
        pipeline = [
            {"$match": match},
            {"$group": {"_id": {"resource_id": "$resource_id", "action": "$action"}, "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 2000},
        ]
        rows: list[dict] = []
        collection = LibraryDigitalAccessLog.get_motor_collection()
        async for row in collection.aggregate(pipeline):
            key = row["_id"]
            title = None
            res = await LibraryDigitalResource.find_one({"tenant_id": ctx.tenant_id, "resource_id": key["resource_id"]})
            if res:
                title = res.title
            rows.append(
                {
                    "resource_id": key["resource_id"],
                    "title": title,
                    "action": key["action"],
                    "event_count": row["count"],
                }
            )
        return rows, {"usage_rows": len(rows)}

    async def _branch_performance(self, ctx: LibraryReportContext) -> tuple[list[dict], dict]:
        dash_ctx = await build_dashboard_context(
            ctx.tenant_id,
            branch_code=None,
            category=ctx.category,
            copy_status=None,
            anchor_date=ctx.date_to,
            date_range=LibraryDashboardDateRange.MONTH,
        )
        summaries = await self._dashboard.branch_inventory(dash_ctx)
        rows = [
            {
                "branch_code": s.branch_code,
                "branch_name": s.branch_name,
                "total_copies": s.total_copies,
                "available": s.available,
                "issued": s.issued,
            }
            for s in summaries
        ]
        if ctx.branch_code:
            rows = [r for r in rows if r["branch_code"] == ctx.branch_code]
        return rows, {"branches": len(rows)}

    async def _popular_books(self, ctx: LibraryReportContext) -> tuple[list[dict], dict]:
        match = {**circulation_match(ctx), "issued_at": {"$gte": ctx.window_start, "$lt": ctx.window_end}}
        pipeline = [
            {"$match": match},
            {"$group": {"_id": {"book_id": "$book_id", "title": "$title"}, "issues": {"$sum": 1}}},
            {"$sort": {"issues": -1}},
            {"$limit": 50},
        ]
        rows: list[dict] = []
        collection = LibraryCirculation.get_motor_collection()
        async for row in collection.aggregate(pipeline):
            key = row["_id"]
            rows.append({"book_id": key["book_id"], "title": key["title"], "issue_count": row["issues"]})
        return rows, {"top_titles": len(rows)}