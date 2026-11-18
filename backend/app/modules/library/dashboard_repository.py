"""MongoDB aggregations for the library dashboard."""

from datetime import date

from beanie import PydanticObjectId

from app.modules.college_admin.identity_models import InstitutionAccountStatus, InstitutionUser
from app.modules.college_admin.library_admin_models import (
    LibraryAcquisition,
    LibraryBookCopyRecord,
    LibraryBranch,
    LibraryCirculationRecord,
    LibraryInventoryHistory,
    LibraryMembershipReference,
)
from app.modules.library.dashboard_filters import (
    LibraryDashboardContext,
    calendar_day_bounds,
    catalogue_match_filters,
    copy_match_filters,
)
from app.modules.library.dashboard_schemas import (
    AcquisitionSummary,
    BranchInventorySummary,
    CatalogueStats,
    CirculationTodayStats,
    CopyInventoryStats,
    DigitalResourceStats,
    LibraryActivityItem,
    LibraryAlertItem,
    LibraryMemberStats,
    OutstandingFineSummary,
    UpcomingDueDateItem,
)
from app.modules.library.library_enums import (
    LibraryCirculationStatus,
    LibraryCopyStatus,
    LibraryFineStatus,
    LibraryReservationStatus,
)
from app.modules.library.member_enums import LibraryMemberStatus
from app.modules.library.library_models import (
    LibraryCatalogItem,
    LibraryCirculation,
    LibraryCopy,
    LibraryDigitalResource,
    LibraryFine,
    LibraryReservation,
)

_PENDING_ACQUISITION_STATUSES = frozenset(
    {
        "ordered",
        "pending",
        "in_transit",
        "submitted",
        "pending_approval",
        "approved",
        "quoted",
        "partial_received",
    }
)


class LibraryDashboardRepository:
    async def catalogue_stats(self, ctx: LibraryDashboardContext) -> CatalogueStats:
        match = catalogue_match_filters(ctx)
        if ctx.branch_code and ctx.scoped_copy_ids is not None:
            if not ctx.scoped_copy_ids:
                return CatalogueStats(total_titles=0)
            copy_rows = await LibraryBookCopyRecord.find(
                {"tenant_id": ctx.tenant_id, "branch_code": ctx.branch_code},
            ).to_list()
            book_ids = {row.book_id for row in copy_rows}
            if not book_ids:
                return CatalogueStats(total_titles=0)
            if ctx.scoped_book_ids is not None:
                book_ids &= set(ctx.scoped_book_ids)
            if not book_ids:
                return CatalogueStats(total_titles=0)
            match["book_id"] = {"$in": list(book_ids)}
        count = await LibraryCatalogItem.find(match).count()
        return CatalogueStats(total_titles=count)

    async def copy_inventory(self, ctx: LibraryDashboardContext) -> CopyInventoryStats:
        if ctx.scoped_copy_ids is not None and len(ctx.scoped_copy_ids) == 0:
            return CopyInventoryStats(
                total_copies=0,
                available=0,
                issued=0,
                overdue_loans=0,
                reserved=0,
                lost=0,
                damaged=0,
            )
        collection = LibraryCopy.get_motor_collection()
        pipeline = [
            {"$match": copy_match_filters(ctx)},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        status_counts: dict[str, int] = {}
        async for row in collection.aggregate(pipeline):
            status_counts[row["_id"]] = row["count"]

        total = sum(status_counts.values())
        overdue_loans = await self._overdue_loan_count(ctx)
        return CopyInventoryStats(
            total_copies=total,
            available=status_counts.get(LibraryCopyStatus.AVAILABLE.value, 0),
            issued=status_counts.get(LibraryCopyStatus.ISSUED.value, 0),
            overdue_loans=overdue_loans,
            reserved=status_counts.get(LibraryCopyStatus.RESERVED.value, 0),
            lost=status_counts.get(LibraryCopyStatus.LOST.value, 0),
            damaged=status_counts.get(LibraryCopyStatus.DAMAGED.value, 0)
            + status_counts.get(LibraryCopyStatus.MAINTENANCE.value, 0),
        )

    async def _overdue_loan_count(self, ctx: LibraryDashboardContext) -> int:
        today = date.today()
        match: dict = {
            "tenant_id": ctx.tenant_id,
            "status": {"$in": [LibraryCirculationStatus.ACTIVE.value, LibraryCirculationStatus.OVERDUE.value]},
            "due_at": {"$lt": today},
        }
        if ctx.scoped_copy_ids is not None:
            match["copy_id"] = {"$in": list(ctx.scoped_copy_ids)}
        if ctx.scoped_book_ids is not None:
            match["book_id"] = {"$in": list(ctx.scoped_book_ids)}
        return await LibraryCirculation.find(match).count()

    async def member_stats(self, ctx: LibraryDashboardContext) -> LibraryMemberStats:
        membership_query: dict = {"tenant_id": ctx.tenant_id}
        if ctx.branch_code:
            membership_query["branch_code"] = ctx.branch_code
        members = await LibraryMembershipReference.find(membership_query).to_list()
        if not members:
            return LibraryMemberStats(total=0, active=0, inactive=0, suspended=0)

        user_ids = [m.member_user_id for m in members]
        institution_rows = await InstitutionUser.find(
            {"tenant_id": ctx.tenant_id, "user_id": {"$in": user_ids}},
        ).to_list()
        institution_by_user = {row.user_id: row for row in institution_rows}

        active = inactive = suspended = 0
        for member in members:
            institution = institution_by_user.get(member.member_user_id)
            if member.status == LibraryMemberStatus.SUSPENDED.value or (
                institution and institution.account_status == InstitutionAccountStatus.SUSPENDED
            ):
                suspended += 1
            elif (
                member.status == LibraryMemberStatus.ACTIVE.value
                and member.eligible
                and (institution is None or institution.account_status == InstitutionAccountStatus.ACTIVE)
            ):
                active += 1
            else:
                inactive += 1

        return LibraryMemberStats(
            total=len(members),
            active=active,
            inactive=inactive,
            suspended=suspended,
        )

    async def circulation_today(self, ctx: LibraryDashboardContext, *, activity_day: date) -> CirculationTodayStats:
        day_start, day_end = calendar_day_bounds(activity_day)
        base_match: dict = {"tenant_id": ctx.tenant_id}
        if ctx.scoped_copy_ids is not None:
            base_match["copy_id"] = {"$in": list(ctx.scoped_copy_ids)}
        if ctx.scoped_book_ids is not None:
            base_match["book_id"] = {"$in": list(ctx.scoped_book_ids)}

        issues = await LibraryCirculation.find({**base_match, "issued_at": {"$gte": day_start, "$lt": day_end}}).count()
        returns = await LibraryCirculation.find({**base_match, "returned_at": {"$gte": day_start, "$lt": day_end}}).count()
        return CirculationTodayStats(issues=issues, returns=returns, activity_date=activity_day)

    async def pending_reservations(self, ctx: LibraryDashboardContext) -> int:
        match: dict = {
            "tenant_id": ctx.tenant_id,
            "status": {"$in": [LibraryReservationStatus.QUEUED.value, LibraryReservationStatus.READY.value]},
        }
        if ctx.scoped_book_ids is not None:
            match["book_id"] = {"$in": list(ctx.scoped_book_ids)}
        return await LibraryReservation.find(match).count()

    async def outstanding_fines(self, ctx: LibraryDashboardContext) -> OutstandingFineSummary:
        collection = LibraryFine.get_motor_collection()
        match: dict = {"tenant_id": ctx.tenant_id, "status": LibraryFineStatus.OPEN.value}
        pipeline = [
            {"$match": match},
            {"$group": {"_id": None, "count": {"$sum": 1}, "total": {"$sum": "$amount"}}},
        ]
        async for row in collection.aggregate(pipeline):
            return OutstandingFineSummary(open_count=row["count"], total_amount=round(float(row["total"]), 2))
        return OutstandingFineSummary(open_count=0, total_amount=0.0)

    async def acquisition_summary(self, ctx: LibraryDashboardContext) -> AcquisitionSummary:
        match: dict = {
            "tenant_id": ctx.tenant_id,
            "created_at": {"$gte": ctx.window_start, "$lt": ctx.window_end},
        }
        if ctx.branch_code:
            match["branch_code"] = ctx.branch_code
        recent_count = await LibraryAcquisition.find(match).count()
        pending_match: dict = {
            "tenant_id": ctx.tenant_id,
            "status": {"$in": list(_PENDING_ACQUISITION_STATUSES)},
        }
        if ctx.branch_code:
            pending_match["branch_code"] = ctx.branch_code
        pending = await LibraryAcquisition.find(pending_match).count()
        return AcquisitionSummary(recent_count=recent_count, pending_procurement_count=pending)

    async def digital_stats(self, ctx: LibraryDashboardContext) -> DigitalResourceStats:
        base = {"tenant_id": ctx.tenant_id}
        total = await LibraryDigitalResource.find(base).count()
        published = await LibraryDigitalResource.find({**base, "published": True}).count()
        return DigitalResourceStats(total=total, published=published, unpublished=total - published)

    async def branch_inventory(self, ctx: LibraryDashboardContext) -> list[BranchInventorySummary]:
        if ctx.branch_code:
            branch = await LibraryBranch.find_one({"tenant_id": ctx.tenant_id, "branch_code": ctx.branch_code})
            name = branch.name if branch else None
            return [await self._branch_summary(ctx.tenant_id, ctx.branch_code, name)]

        branches = await LibraryBranch.find({"tenant_id": ctx.tenant_id, "is_active": True}).to_list()
        if not branches:
            unassigned = await self._branch_summary(ctx.tenant_id, None)
            return [unassigned] if unassigned.total_copies else []

        summaries: list[BranchInventorySummary] = []
        for branch in branches:
            summaries.append(await self._branch_summary(ctx.tenant_id, branch.branch_code, branch.name))
        unassigned = await self._branch_summary(ctx.tenant_id, None)
        if unassigned.total_copies:
            summaries.append(unassigned)
        return summaries

    async def _branch_summary(
        self,
        tenant_id: PydanticObjectId,
        branch_code: str | None,
        branch_name: str | None = None,
    ) -> BranchInventorySummary:
        if branch_code:
            copy_rows = await LibraryBookCopyRecord.find(
                {"tenant_id": tenant_id, "branch_code": branch_code},
            ).to_list()
        else:
            copy_rows = await LibraryBookCopyRecord.find(
                {"tenant_id": tenant_id, "$or": [{"branch_code": None}, {"branch_code": {"$exists": False}}]},
            ).to_list()
        copy_ids = [r.copy_id for r in copy_rows]
        if not copy_ids:
            return BranchInventorySummary(
                branch_code=branch_code,
                branch_name=branch_name,
                total_copies=0,
                available=0,
                issued=0,
            )
        collection = LibraryCopy.get_motor_collection()
        pipeline = [
            {"$match": {"tenant_id": tenant_id, "copy_id": {"$in": copy_ids}}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        status_counts: dict[str, int] = {}
        async for row in collection.aggregate(pipeline):
            status_counts[row["_id"]] = row["count"]
        total = sum(status_counts.values())
        return BranchInventorySummary(
            branch_code=branch_code,
            branch_name=branch_name,
            total_copies=total,
            available=status_counts.get(LibraryCopyStatus.AVAILABLE.value, 0),
            issued=status_counts.get(LibraryCopyStatus.ISSUED.value, 0),
        )

    async def upcoming_due_dates(
        self,
        ctx: LibraryDashboardContext,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[UpcomingDueDateItem], int]:
        match: dict = {
            "tenant_id": ctx.tenant_id,
            "status": {"$in": [LibraryCirculationStatus.ACTIVE.value, LibraryCirculationStatus.OVERDUE.value]},
            "due_at": {"$gte": ctx.anchor_date},
        }
        if ctx.scoped_copy_ids is not None:
            match["copy_id"] = {"$in": list(ctx.scoped_copy_ids)}
        if ctx.scoped_book_ids is not None:
            match["book_id"] = {"$in": list(ctx.scoped_book_ids)}

        query = LibraryCirculation.find(match).sort("due_at")
        total = await query.count()
        rows = await query.skip(offset).limit(limit).to_list()
        items = [
            UpcomingDueDateItem(
                circulation_id=row.circulation_id,
                book_id=row.book_id,
                copy_id=row.copy_id,
                title=row.title,
                due_at=row.due_at,
                student_user_id=str(row.student_user_id),
            )
            for row in rows
        ]
        return items, total

    async def recent_activities(
        self,
        ctx: LibraryDashboardContext,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[LibraryActivityItem], int]:
        circulation_query: dict = {
            "tenant_id": ctx.tenant_id,
            "created_at": {"$gte": ctx.window_start, "$lt": ctx.window_end},
        }
        inventory_query: dict = {
            "tenant_id": ctx.tenant_id,
            "created_at": {"$gte": ctx.window_start, "$lt": ctx.window_end},
        }
        if ctx.branch_code:
            circulation_query["branch_code"] = ctx.branch_code
            inventory_query["branch_code"] = ctx.branch_code

        circ_rows = await LibraryCirculationRecord.find(circulation_query).sort("-created_at").limit(250).to_list()
        inv_rows = await LibraryInventoryHistory.find(inventory_query).sort("-created_at").limit(250).to_list()

        combined: list[LibraryActivityItem] = []
        for row in circ_rows:
            combined.append(
                LibraryActivityItem(
                    activity_id=f"circ_{row.circulation_id}_{row.created_at.timestamp():.0f}",
                    event_type=row.action,
                    summary=f"Circulation {row.action}: {row.circulation_id}",
                    branch_code=row.branch_code,
                    actor_id=str(row.actor_id) if row.actor_id else None,
                    created_at=row.created_at,
                )
            )
        for row in inv_rows:
            combined.append(
                LibraryActivityItem(
                    activity_id=f"inv_{row.id!s}",
                    event_type=row.event_type,
                    summary=row.note or row.event_type.replace("_", " ").title(),
                    branch_code=row.branch_code,
                    actor_id=str(row.actor_id) if row.actor_id else None,
                    created_at=row.created_at,
                )
            )

        combined.sort(key=lambda item: item.created_at, reverse=True)
        total = len(combined)
        page = combined[offset : offset + limit]
        return page, total

    async def alerts(self, ctx: LibraryDashboardContext) -> list[LibraryAlertItem]:
        copies = await self.copy_inventory(ctx)
        pending_res = await self.pending_reservations(ctx)
        acquisitions = await self.acquisition_summary(ctx)
        alerts: list[LibraryAlertItem] = []

        if copies.overdue_loans:
            alerts.append(
                LibraryAlertItem(
                    code="overdue_loans",
                    severity="high",
                    message="Active loans past due date",
                    count=copies.overdue_loans,
                )
            )
        if copies.lost:
            alerts.append(
                LibraryAlertItem(
                    code="lost_copies",
                    severity="medium",
                    message="Copies marked lost",
                    count=copies.lost,
                )
            )
        if pending_res:
            alerts.append(
                LibraryAlertItem(
                    code="pending_reservations",
                    severity="medium",
                    message="Reservations awaiting fulfilment",
                    count=pending_res,
                )
            )
        if acquisitions.pending_procurement_count:
            alerts.append(
                LibraryAlertItem(
                    code="pending_procurement",
                    severity="low",
                    message="Acquisition orders not yet received",
                    count=acquisitions.pending_procurement_count,
                )
            )
        if ctx.scoped_copy_ids is not None and copies.total_copies == 0:
            alerts.append(
                LibraryAlertItem(
                    code="empty_branch_inventory",
                    severity="low",
                    message="No physical copies for the selected branch scope",
                    count=0,
                )
            )
        return alerts