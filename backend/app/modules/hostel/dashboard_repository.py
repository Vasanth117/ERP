"""Hostel dashboard aggregation repository."""

from datetime import datetime, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.modules.college_admin.hostel_admin_models import (
    HostelAllocation,
    HostelAllocationStatus,
    HostelBed,
    HostelBedStatus,
    HostelBlock,
    HostelBuilding,
    HostelIncident,
    HostelMaintenanceRequest,
    HostelMessPlan,
    HostelOutpassRequest,
    HostelResidentHistory,
    HostelRoom,
    HostelVisitorLog,
    HostelWaitingListEntry,
)
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.hostel.dashboard_filters import HostelDashboardContext
from app.modules.hostel.dashboard_schemas import (
    AllocationOverviewStats,
    HostelActivityItem,
    HostelAlertItem,
    HostelOverviewStats,
    IncidentOverviewStats,
    LeaveOutpassOverviewStats,
    MaintenanceOverviewStats,
    MessOverviewStats,
    OccupancyBreakdownItem,
    ResidentOverviewStats,
    VisitorOverviewStats,
)
from app.modules.hostel.hostel_enums import HostelApplicationStatus, HostelRequestStatus, HostelRequestType
from app.modules.hostel.leave_outpass_models import HostelLeaveOutpassStatus
from app.modules.hostel.maintenance_models import HostelComplaint, HostelComplaintPriority, HostelComplaintStatus
from app.modules.hostel.mess_models import HostelMessEnrollment, MessEnrollmentStatus
from app.modules.hostel.rules_incident_models import HostelIncidentSeverity, HostelIncidentStatus
from app.modules.hostel.hostel_models import HostelApplication, HostelNotice, HostelServiceRequest
from app.modules.hostel.infrastructure_models import HostelFloor, InstitutionHostel
from app.modules.hostel.resident_models import HostelResident, HostelResidentStatus
from app.modules.hostel.visitor_models import HostelVisitorEntry, HostelVisitorStatus
from app.modules.students.models import StudentProfile


class HostelDashboardRepository:
    async def resolve_building_codes(self, ctx: HostelDashboardContext) -> list[str] | None:
        if ctx.building_code:
            return [ctx.building_code]
        if ctx.hostel_code:
            rows = await HostelBuilding.find(
                {"tenant_id": ctx.tenant_id, "hostel_code": ctx.hostel_code}
            ).to_list()
            codes = [r.building_code for r in rows]
            ctx.building_codes = codes
            return codes if codes else None
        return None

    def _bed_query(self, ctx: HostelDashboardContext, building_codes: list[str] | None) -> dict:
        query: dict = {"tenant_id": ctx.tenant_id}
        if building_codes:
            query["building_code"] = {"$in": building_codes}
        if ctx.block_code:
            query["block_code"] = ctx.block_code
        if ctx.hostel_code and not building_codes:
            query["hostel_code"] = ctx.hostel_code
        return query

    async def hostel_overview(self, ctx: HostelDashboardContext) -> HostelOverviewStats:
        building_codes = await self.resolve_building_codes(ctx)
        hostel_query = {"tenant_id": ctx.tenant_id}
        if ctx.hostel_code:
            hostel_query["hostel_code"] = ctx.hostel_code
        hostels = await InstitutionHostel.find(hostel_query).to_list()
        total_hostels = len(hostels)
        active_hostels = sum(1 for h in hostels if h.is_active and h.operating_status.value == "active")
        inactive_hostels = total_hostels - active_hostels

        building_filter: dict = {"tenant_id": ctx.tenant_id}
        if building_codes:
            building_filter["building_code"] = {"$in": building_codes}
        elif ctx.hostel_code:
            building_filter["hostel_code"] = ctx.hostel_code

        total_buildings = await HostelBuilding.find(building_filter).count()
        total_blocks = await HostelBlock.find(
            {**building_filter, **({"building_code": ctx.building_code} if ctx.building_code else {})}
        ).count()

        floor_filter: dict = {"tenant_id": ctx.tenant_id}
        if ctx.hostel_code:
            floor_filter["hostel_code"] = ctx.hostel_code
        if ctx.building_code:
            floor_filter["building_code"] = ctx.building_code
        if ctx.floor_id:
            floor_filter["floor_id"] = ctx.floor_id
        total_floors = await HostelFloor.find(floor_filter).count()

        room_filter: dict = {"tenant_id": ctx.tenant_id}
        if building_codes:
            room_filter["building_code"] = {"$in": building_codes}
        if ctx.block_code:
            room_filter["block_code"] = ctx.block_code
        if ctx.floor_id:
            room_filter["floor_id"] = ctx.floor_id
        if ctx.room_type:
            room_filter["room_type"] = ctx.room_type
        total_rooms = await HostelRoom.find(room_filter).count()

        bed_query = self._bed_query(ctx, building_codes)
        total_beds = await HostelBed.find(bed_query).count()
        occupied = await HostelBed.find({**bed_query, "status": HostelBedStatus.ALLOCATED.value}).count()
        available = await HostelBed.find({**bed_query, "status": HostelBedStatus.AVAILABLE.value}).count()
        reserved = await HostelBed.find({**bed_query, "status": HostelBedStatus.RESERVED.value}).count()
        maintenance = await HostelBed.find({**bed_query, "status": HostelBedStatus.MAINTENANCE.value}).count()
        denom = max(total_beds, 1)
        pct = round((occupied + reserved) / denom * 100, 2)

        by_hostel: list[OccupancyBreakdownItem] = []
        for h in hostels:
            codes = [b.building_code for b in await HostelBuilding.find({"tenant_id": ctx.tenant_id, "hostel_code": h.hostel_code}).to_list()]
            bq = {"tenant_id": ctx.tenant_id}
            if codes:
                bq["$or"] = [{"hostel_code": h.hostel_code}, {"building_code": {"$in": codes}}]
            else:
                bq["hostel_code"] = h.hostel_code
            t = await HostelBed.find(bq).count()
            occ = await HostelBed.find({**bq, "status": HostelBedStatus.ALLOCATED.value}).count()
            av = await HostelBed.find({**bq, "status": HostelBedStatus.AVAILABLE.value}).count()
            by_hostel.append(
                OccupancyBreakdownItem(
                    key=h.hostel_code,
                    label=h.name,
                    total_beds=t,
                    occupied_beds=occ,
                    available_beds=av,
                    occupancy_percentage=round(occ / max(t, 1) * 100, 2),
                )
            )

        by_block: list[OccupancyBreakdownItem] = []
        blocks = await HostelBlock.find(building_filter if not ctx.building_code else {"tenant_id": ctx.tenant_id, "building_code": ctx.building_code}).to_list()
        for bl in blocks[:50]:
            bq = {
                "tenant_id": ctx.tenant_id,
                "building_code": bl.building_code,
                "block_code": bl.block_code,
            }
            t = await HostelBed.find(bq).count()
            occ = await HostelBed.find({**bq, "status": HostelBedStatus.ALLOCATED.value}).count()
            av = await HostelBed.find({**bq, "status": HostelBedStatus.AVAILABLE.value}).count()
            by_block.append(
                OccupancyBreakdownItem(
                    key=f"{bl.building_code}:{bl.block_code}",
                    label=bl.name,
                    total_beds=t,
                    occupied_beds=occ,
                    available_beds=av,
                    occupancy_percentage=round(occ / max(t, 1) * 100, 2),
                )
            )

        by_floor: list[OccupancyBreakdownItem] = []
        floors = await HostelFloor.find(floor_filter).sort("sort_order").limit(50).to_list()
        for fl in floors:
            rq = {
                "tenant_id": ctx.tenant_id,
                "building_code": fl.building_code,
                "floor_id": fl.floor_id,
            }
            rooms = await HostelRoom.find(rq).to_list()
            room_keys = {(r.building_code, r.block_code, r.room_code) for r in rooms}
            t = occ = av = 0
            for bc, blc, rc in room_keys:
                bq = {"tenant_id": ctx.tenant_id, "building_code": bc, "block_code": blc, "room_code": rc}
                t += await HostelBed.find(bq).count()
                occ += await HostelBed.find({**bq, "status": HostelBedStatus.ALLOCATED.value}).count()
                av += await HostelBed.find({**bq, "status": HostelBedStatus.AVAILABLE.value}).count()
            by_floor.append(
                OccupancyBreakdownItem(
                    key=fl.floor_id,
                    label=fl.name,
                    total_beds=t,
                    occupied_beds=occ,
                    available_beds=av,
                    occupancy_percentage=round(occ / max(t, 1) * 100, 2),
                )
            )

        return HostelOverviewStats(
            total_hostels=total_hostels,
            active_hostels=active_hostels,
            inactive_hostels=inactive_hostels,
            total_buildings=total_buildings,
            total_blocks=total_blocks,
            total_floors=total_floors,
            total_rooms=total_rooms,
            total_beds=total_beds,
            occupied_beds=occupied,
            available_beds=available,
            reserved_beds=reserved,
            maintenance_beds=maintenance,
            occupancy_percentage=pct,
            by_hostel=by_hostel,
            by_block=by_block,
            by_floor=by_floor,
        )

    async def _student_ids_for_department(self, ctx: HostelDashboardContext) -> list[PydanticObjectId] | None:
        if ctx.department_id is None:
            return None
        profiles = await StudentProfile.find(
            Eq(StudentProfile.tenant_id, ctx.tenant_id),
            Eq(StudentProfile.department_id, ctx.department_id),
        ).to_list()
        return [p.user_id for p in profiles]

    def _allocation_filter(self, ctx: HostelDashboardContext, building_codes: list[str] | None) -> dict:
        q: dict = {"tenant_id": ctx.tenant_id}
        if building_codes:
            q["building_code"] = {"$in": building_codes}
        if ctx.block_code:
            q["block_code"] = ctx.block_code
        if ctx.allocation_status:
            q["status"] = ctx.allocation_status
        return q

    async def resident_overview(self, ctx: HostelDashboardContext) -> ResidentOverviewStats:
        building_codes = await self.resolve_building_codes(ctx)
        student_ids = await self._student_ids_for_department(ctx)
        base = self._allocation_filter(ctx, building_codes)

        async def count_status(status: HostelAllocationStatus) -> int:
            expr = [
                Eq(HostelAllocation.tenant_id, ctx.tenant_id),
                Eq(HostelAllocation.status, status),
            ]
            if building_codes and building_codes != ["__none__"]:
                expr.append(In(HostelAllocation.building_code, building_codes))
            elif ctx.building_code:
                expr.append(Eq(HostelAllocation.building_code, ctx.building_code))
            if student_ids is not None:
                expr.append(In(HostelAllocation.student_user_id, student_ids))
            return await HostelAllocation.find(*expr).count()

        active = await count_status(HostelAllocationStatus.ACTIVE)
        pending = await count_status(HostelAllocationStatus.PENDING)
        checked_out = await count_status(HostelAllocationStatus.CHECKED_OUT)
        cancelled = await count_status(HostelAllocationStatus.CANCELLED)
        total_registered = active + pending + checked_out

        app_q: dict = {"tenant_id": ctx.tenant_id}
        if ctx.academic_year_label:
            app_q["academic_year_label"] = ctx.academic_year_label
        if student_ids is not None:
            app_q["student_user_id"] = {"$in": student_ids}
        pending_apps = await HostelApplication.find(
            {**app_q, "status": HostelApplicationStatus.SUBMITTED.value}
        ).count()

        now = datetime.now(timezone.utc)
        approved = HostelLeaveOutpassStatus.APPROVED.value
        outpass_q: dict = {"tenant_id": ctx.tenant_id, "status": approved, "to_at": {"$gte": now}}
        if student_ids is not None:
            outpass_q["student_user_id"] = {"$in": student_ids}
        on_outpass = await HostelOutpassRequest.find(outpass_q).count()
        overdue_outpass = await HostelOutpassRequest.find(
            {
                "tenant_id": ctx.tenant_id,
                "status": approved,
                "to_at": {"$lt": now},
                **({"student_user_id": {"$in": student_ids}} if student_ids is not None else {}),
            }
        ).count()

        return ResidentOverviewStats(
            total_registered_residents=total_registered,
            checked_in_residents=active,
            awaiting_check_in=pending,
            checked_out_residents=checked_out,
            upcoming_checkouts=0,
            on_approved_outpass=on_outpass,
            overdue_outpasses=overdue_outpass,
            pending_applications=pending_apps,
        )

    async def allocation_overview(self, ctx: HostelDashboardContext) -> AllocationOverviewStats:
        building_codes = await self.resolve_building_codes(ctx)
        student_ids = await self._student_ids_for_department(ctx)
        pending_req = await HostelServiceRequest.find(
            {
                "tenant_id": ctx.tenant_id,
                "request_type": HostelRequestType.ROOM_CHANGE.value,
                "status": {"$in": [HostelRequestStatus.SUBMITTED.value, HostelRequestStatus.UNDER_REVIEW.value]},
            }
        ).count()

        app_q: dict = {"tenant_id": ctx.tenant_id, "status": HostelApplicationStatus.APPROVED.value}
        if ctx.academic_year_label:
            app_q["academic_year_label"] = ctx.academic_year_label
        approved_wait = await HostelApplication.find(app_q).count()
        waiting = await HostelWaitingListEntry.find(Eq(HostelWaitingListEntry.tenant_id, ctx.tenant_id)).count()

        bed_q = self._bed_query(ctx, building_codes)
        available_beds = await HostelBed.find({**bed_q, "status": HostelBedStatus.AVAILABLE.value}).to_list()
        by_type: dict[str, int] = {}
        for bed in available_beds:
            room = await HostelRoom.find_one(
                Eq(HostelRoom.tenant_id, ctx.tenant_id),
                Eq(HostelRoom.building_code, bed.building_code),
                Eq(HostelRoom.block_code, bed.block_code),
                Eq(HostelRoom.room_code, bed.room_code),
            )
            rt = room.room_type if room and room.room_type else "unknown"
            by_type[rt] = by_type.get(rt, 0) + 1

        alloc_q = self._allocation_filter(ctx, building_codes)
        alloc_coll = HostelAllocation.get_motor_collection()
        recent = await alloc_coll.count_documents(
            {**alloc_q, "created_at": {"$gte": ctx.range_start, "$lte": ctx.range_end}}
        )
        cancelled = await alloc_coll.count_documents(
            {**alloc_q, "status": HostelAllocationStatus.CANCELLED.value}
        )

        rooms_unassigned = await HostelRoom.find(
            {
                "tenant_id": ctx.tenant_id,
                **({"building_code": {"$in": building_codes}} if building_codes else {}),
                "operational_status": "active",
            }
        ).count()

        return AllocationOverviewStats(
            pending_allocation_requests=pending_req,
            approved_awaiting_allocation=approved_wait,
            waiting_list_students=waiting,
            rooms_awaiting_assignment=rooms_unassigned,
            available_beds_by_type=by_type,
            recent_allocations=recent,
            pending_room_transfers=pending_req,
            cancelled_allocations=cancelled,
        )

    async def mess_overview(self, ctx: HostelDashboardContext) -> MessOverviewStats:
        active_plans = await HostelMessPlan.find(
            {"tenant_id": ctx.tenant_id, "published": True}
        ).count()
        enrolled = await HostelMessEnrollment.find(
            {"tenant_id": ctx.tenant_id, "status": MessEnrollmentStatus.ACTIVE.value}
        ).count()
        active_residents = await HostelAllocation.find(
            {"tenant_id": ctx.tenant_id, "status": HostelAllocationStatus.ACTIVE.value}
        ).count()
        pending_enroll = await HostelMessEnrollment.find(
            {"tenant_id": ctx.tenant_id, "status": MessEnrollmentStatus.PENDING_APPROVAL.value}
        ).count()
        mess_demands = await StudentFeeDemand.find(
            {
                "tenant_id": ctx.tenant_id,
                "status": FeeDemandStatus.OPEN.value,
                "description": {"$regex": "mess", "$options": "i"},
            }
        ).to_list()
        outstanding = sum(d.amount for d in mess_demands)
        return MessOverviewStats(
            active_mess_plans=active_plans,
            residents_enrolled=enrolled,
            residents_without_mess=max(active_residents - enrolled, 0),
            billing_period_label=ctx.academic_year_label,
            pending_billing_records=len(mess_demands),
            outstanding_mess_charges=outstanding,
            plan_changes_pending_approval=pending_enroll,
        )

    async def visitor_overview(self, ctx: HostelDashboardContext) -> VisitorOverviewStats:
        building_codes = await self.resolve_building_codes(ctx)
        day_start = datetime.combine(ctx.anchor_date, datetime.min.time(), tzinfo=timezone.utc)
        day_end = datetime.combine(ctx.anchor_date, datetime.max.time(), tzinfo=timezone.utc)
        base: dict = {"tenant_id": ctx.tenant_id}
        today = await HostelVisitorLog.find({**base, "check_in_at": {"$gte": day_start, "$lte": day_end}}).count()
        inside_legacy = await HostelVisitorLog.find({**base, "check_out_at": None}).count()
        inside_new = await HostelVisitorEntry.find(
            {"tenant_id": ctx.tenant_id, "status": HostelVisitorStatus.INSIDE.value}
        ).count()
        inside = max(inside_legacy, inside_new)
        incomplete = await HostelVisitorLog.find(
            {**base, "check_in_at": {"$lt": day_start}, "check_out_at": None}
        ).count()
        recent = await HostelVisitorLog.find(
            {**base, "check_in_at": {"$gte": ctx.range_start, "$lte": ctx.range_end}}
        ).count()
        _ = building_codes
        return VisitorOverviewStats(
            visitors_today=today,
            currently_inside=inside,
            expected_visitors=0,
            awaiting_approval=0,
            incomplete_checkout=incomplete,
            recent_activity_count=recent,
        )

    async def maintenance_overview(self, ctx: HostelDashboardContext) -> MaintenanceOverviewStats:
        building_codes = await self.resolve_building_codes(ctx)
        base: dict = {"tenant_id": ctx.tenant_id}
        if building_codes:
            base["building_code"] = {"$in": building_codes}
        if ctx.maintenance_status:
            base["status"] = ctx.maintenance_status
        open_statuses = [
            HostelComplaintStatus.SUBMITTED.value,
            HostelComplaintStatus.ASSIGNED.value,
            HostelComplaintStatus.ACKNOWLEDGED.value,
            HostelComplaintStatus.REOPENED.value,
        ]
        q = {"tenant_id": ctx.tenant_id, "status": {"$in": open_statuses}}
        if building_codes:
            q["building_code"] = {"$in": building_codes}
        open_count = await HostelComplaint.find(q).count()
        in_progress = await HostelComplaint.find(
            {"tenant_id": ctx.tenant_id, "status": HostelComplaintStatus.IN_PROGRESS.value}
        ).count()
        resolved = await HostelComplaint.find(
            {
                "tenant_id": ctx.tenant_id,
                "status": {"$in": [HostelComplaintStatus.RESOLVED.value, HostelComplaintStatus.CLOSED.value]},
                "created_at": {"$gte": ctx.range_start},
            }
        ).count()
        high_pri = await HostelComplaint.find(
            {
                "tenant_id": ctx.tenant_id,
                "priority": {"$in": [HostelComplaintPriority.HIGH.value, HostelComplaintPriority.CRITICAL.value]},
                "status": {"$nin": [HostelComplaintStatus.CLOSED.value, HostelComplaintStatus.REJECTED.value]},
            }
        ).count()
        unavailable_beds = await HostelBed.find(
            {
                "tenant_id": ctx.tenant_id,
                **({"building_code": {"$in": building_codes}} if building_codes else {}),
                "status": HostelBedStatus.MAINTENANCE.value,
            }
        ).count()
        unavailable_rooms = await HostelRoom.find(
            {
                "tenant_id": ctx.tenant_id,
                **({"building_code": {"$in": building_codes}} if building_codes else {}),
                "maintenance_status": "unavailable",
            }
        ).count()
        return MaintenanceOverviewStats(
            open_complaints=open_count,
            high_priority=high_pri,
            in_progress=in_progress,
            pending_assignments=open_count,
            unavailable_rooms=unavailable_rooms,
            unavailable_beds=unavailable_beds,
            overdue_tasks=0,
            recently_resolved=resolved,
        )

    async def leave_outpass_overview(self, ctx: HostelDashboardContext) -> LeaveOutpassOverviewStats:
        pending_leave = await HostelServiceRequest.find(
            {
                "tenant_id": ctx.tenant_id,
                "request_type": HostelRequestType.LEAVE.value,
                "status": HostelRequestStatus.SUBMITTED.value,
            }
        ).count()
        pending_outpass = await HostelOutpassRequest.find(
            {"tenant_id": ctx.tenant_id, "status": "pending"}
        ).count()
        now = datetime.now(timezone.utc)
        active_outpass = await HostelOutpassRequest.find(
            {"tenant_id": ctx.tenant_id, "status": HostelLeaveOutpassStatus.APPROVED.value, "from_at": {"$lte": now}, "to_at": {"$gte": now}}
        ).count()
        overdue = await HostelOutpassRequest.find(
            {"tenant_id": ctx.tenant_id, "status": HostelLeaveOutpassStatus.APPROVED.value, "to_at": {"$lt": now}}
        ).count()
        return LeaveOutpassOverviewStats(
            pending_leave_requests=pending_leave,
            pending_outpass_approvals=pending_outpass,
            approved_outpasses_active=active_outpass,
            students_returned=0,
            overdue_returns=overdue,
        )

    async def incident_overview(self, ctx: HostelDashboardContext) -> IncidentOverviewStats:
        base: dict = {"tenant_id": ctx.tenant_id}
        open_i = await HostelIncident.find(
            {**base, "status": {"$in": [HostelIncidentStatus.REPORTED.value, HostelIncidentStatus.ACKNOWLEDGED.value, HostelIncidentStatus.UNDER_REVIEW.value]}}
        ).count()
        investigating = await HostelIncident.find({**base, "status": HostelIncidentStatus.UNDER_INVESTIGATION.value}).count()
        serious = await HostelIncident.find(
            {
                **base,
                "severity": {"$in": [HostelIncidentSeverity.HIGH.value, HostelIncidentSeverity.CRITICAL.value]},
                "status": {"$nin": [HostelIncidentStatus.CLOSED.value, HostelIncidentStatus.DISMISSED.value]},
            }
        ).count()
        recent = await HostelIncident.find(
            {**base, "created_at": {"$gte": ctx.range_start, "$lte": ctx.range_end}}
        ).count()
        return IncidentOverviewStats(
            open_incidents=open_i,
            under_investigation=investigating,
            serious_incidents=serious,
            pending_disciplinary_reviews=0,
            recent_incidents=recent,
        )

    async def recent_activities(self, ctx: HostelDashboardContext, limit: int = 20) -> list[HostelActivityItem]:
        items: list[HostelActivityItem] = []
        history = await HostelResidentHistory.find(
            {"tenant_id": ctx.tenant_id, "created_at": {"$gte": ctx.range_start}}
        ).sort("-created_at").limit(limit).to_list()
        for h in history:
            items.append(
                HostelActivityItem(
                    activity_id=f"rh_{h.id}",
                    category="resident",
                    title=h.event_type.replace("_", " ").title(),
                    occurred_at=h.created_at,
                    metadata={"allocation_id": h.allocation_id, "student_user_id": str(h.student_user_id)},
                )
            )
        visitors = await HostelVisitorLog.find(
            {"tenant_id": ctx.tenant_id, "check_in_at": {"$gte": ctx.range_start}}
        ).sort("-check_in_at").limit(limit).to_list()
        for v in visitors:
            items.append(
                HostelActivityItem(
                    activity_id=f"vis_{v.visit_id}",
                    category="visitor",
                    title=f"Visitor {v.visitor_name}",
                    occurred_at=v.check_in_at,
                    metadata={"visit_id": v.visit_id},
                )
            )
        notices = await HostelNotice.find({"tenant_id": ctx.tenant_id}).sort("-created_at").limit(5).to_list()
        for n in notices:
            items.append(
                HostelActivityItem(
                    activity_id=f"notice_{n.notice_id}",
                    category="announcement",
                    title=n.title,
                    occurred_at=n.created_at,
                    metadata={"notice_id": n.notice_id},
                )
            )
        items.sort(key=lambda x: x.occurred_at, reverse=True)
        return items[:limit]

    async def alerts(self, ctx: HostelDashboardContext) -> list[HostelAlertItem]:
        alerts: list[HostelAlertItem] = []
        overdue_outpass = await HostelOutpassRequest.find(
            {"tenant_id": ctx.tenant_id, "status": HostelLeaveOutpassStatus.APPROVED.value, "to_at": {"$lt": datetime.now(timezone.utc)}}
        ).count()
        if overdue_outpass:
            alerts.append(
                HostelAlertItem(
                    code="outpass_overdue",
                    severity="warning",
                    title="Overdue outpass",
                    message=f"{overdue_outpass} resident(s) have overdue outpass returns",
                )
            )
        open_maint = await HostelMaintenanceRequest.find({"tenant_id": ctx.tenant_id, "status": "open"}).count()
        if open_maint:
            alerts.append(
                HostelAlertItem(
                    code="maintenance_open",
                    severity="info",
                    title="Open maintenance",
                    message=f"{open_maint} open maintenance request(s)",
                )
            )
        return alerts

    async def drill_down(
        self,
        ctx: HostelDashboardContext,
        metric: str,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[dict], int]:
        building_codes = await self.resolve_building_codes(ctx)
        if metric == "beds_available":
            q = {**self._bed_query(ctx, building_codes), "status": HostelBedStatus.AVAILABLE.value}
            total = await HostelBed.find(q).count()
            rows = await HostelBed.find(q).skip(offset).limit(limit).to_list()
            return [{"bed_id": r.bed_id, "room_code": r.room_code, "status": r.status.value} for r in rows], total
        if metric == "beds_occupied":
            q = {**self._bed_query(ctx, building_codes), "status": HostelBedStatus.ALLOCATED.value}
            total = await HostelBed.find(q).count()
            rows = await HostelBed.find(q).skip(offset).limit(limit).to_list()
            return [{"bed_id": r.bed_id, "room_code": r.room_code, "status": r.status.value} for r in rows], total
        if metric == "applications_pending":
            q = {"tenant_id": ctx.tenant_id, "status": HostelApplicationStatus.SUBMITTED.value}
            if ctx.academic_year_label:
                q["academic_year_label"] = ctx.academic_year_label
            total = await HostelApplication.find(q).count()
            rows = await HostelApplication.find(q).skip(offset).limit(limit).to_list()
            return [{"application_id": r.application_id, "student_user_id": str(r.student_user_id)} for r in rows], total
        if metric == "waiting_list":
            total = await HostelWaitingListEntry.find(Eq(HostelWaitingListEntry.tenant_id, ctx.tenant_id)).count()
            rows = await HostelWaitingListEntry.find(Eq(HostelWaitingListEntry.tenant_id, ctx.tenant_id)).skip(offset).limit(limit).to_list()
            return [{"application_id": r.application_id, "position": r.position} for r in rows], total
        if metric == "visitors_inside":
            total = await HostelVisitorLog.find({"tenant_id": ctx.tenant_id, "check_out_at": None}).count()
            rows = await HostelVisitorLog.find({"tenant_id": ctx.tenant_id, "check_out_at": None}).skip(offset).limit(limit).to_list()
            return [{"visit_id": r.visit_id, "visitor_name": r.visitor_name} for r in rows], total
        if metric == "maintenance_open":
            q = {"tenant_id": ctx.tenant_id, "status": "open"}
            if building_codes:
                q["building_code"] = {"$in": building_codes}
            total = await HostelMaintenanceRequest.find(q).count()
            rows = await HostelMaintenanceRequest.find(q).skip(offset).limit(limit).to_list()
            return [{"request_id": r.request_id, "description": r.description} for r in rows], total
        if metric == "incidents_open":
            total = await HostelIncident.find({"tenant_id": ctx.tenant_id, "status": "open"}).count()
            rows = await HostelIncident.find({"tenant_id": ctx.tenant_id, "status": "open"}).skip(offset).limit(limit).to_list()
            return [{"incident_id": r.incident_id, "severity": r.severity} for r in rows], total
        if metric == "residents_checked_in":
            q = self._allocation_filter(ctx, building_codes)
            q["status"] = HostelAllocationStatus.ACTIVE.value
            alloc_coll = HostelAllocation.get_motor_collection()
            total = await alloc_coll.count_documents(q)
            rows = await HostelAllocation.find(q).skip(offset).limit(limit).to_list()
            return [{"allocation_id": r.allocation_id, "student_user_id": str(r.student_user_id)} for r in rows], total
        if metric == "hostels_active":
            rows = await InstitutionHostel.find({"tenant_id": ctx.tenant_id, "is_active": True}).skip(offset).limit(limit).to_list()
            total = await InstitutionHostel.find({"tenant_id": ctx.tenant_id, "is_active": True}).count()
            return [{"hostel_code": r.hostel_code, "name": r.name} for r in rows], total
        return [], 0