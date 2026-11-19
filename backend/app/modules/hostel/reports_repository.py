"""Hostel report data aggregation (no duplicated operational stores)."""

from beanie import PydanticObjectId

from app.modules.college_admin.hostel_admin_models import HostelBed, HostelBedStatus
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.hostel.hostel_models import HostelApplication
from app.modules.hostel.leave_outpass_models import HostelLeaveRequest, HostelOutpassRequest
from app.modules.hostel.maintenance_models import HostelComplaint
from app.modules.hostel.mess_models import HostelMessBillingRecord, HostelMessEnrollment
from app.modules.hostel.resident_models import HostelResident, HostelResidentStatus
from app.modules.hostel.rules_incident_models import HostelIncident, HostelRuleAcknowledgement
from app.modules.hostel.visitor_models import HostelVisitorEntry, HostelVisitorStatus


class HostelReportsRepository:
    async def occupancy_overview(self, tenant_id: PydanticObjectId, filters: dict) -> list[dict]:
        hostel_code = filters.get("hostel_code")
        bed_q: dict = {"tenant_id": tenant_id}
        if hostel_code:
            bed_q["hostel_code"] = str(hostel_code).upper()
        beds = await HostelBed.find(bed_q).to_list()
        by_building: dict[str, dict] = {}
        for bed in beds:
            key = bed.building_code
            if key not in by_building:
                by_building[key] = {"building_code": key, "total_beds": 0, "available": 0, "allocated": 0, "maintenance": 0}
            by_building[key]["total_beds"] += 1
            if bed.status == HostelBedStatus.AVAILABLE:
                by_building[key]["available"] += 1
            elif bed.status == HostelBedStatus.ALLOCATED:
                by_building[key]["allocated"] += 1
            elif bed.status == HostelBedStatus.MAINTENANCE:
                by_building[key]["maintenance"] += 1
        return list(by_building.values())

    async def applications_summary(self, tenant_id: PydanticObjectId, filters: dict) -> list[dict]:
        q: dict = {"tenant_id": tenant_id}
        if filters.get("academic_year_label"):
            q["academic_year_label"] = filters["academic_year_label"]
        rows = await HostelApplication.find(q).to_list()
        counts: dict[str, int] = {}
        for r in rows:
            counts[r.status.value] = counts.get(r.status.value, 0) + 1
        return [{"status": k, "count": v} for k, v in sorted(counts.items())]

    async def residents_current(self, tenant_id: PydanticObjectId, filters: dict) -> list[dict]:
        q: dict = {"tenant_id": tenant_id}
        if filters.get("hostel_code"):
            q["hostel_code"] = str(filters["hostel_code"]).upper()
        status = filters.get("status")
        if status:
            q["status"] = status
        else:
            q["status"] = {"$in": [HostelResidentStatus.CHECKED_IN.value, HostelResidentStatus.TEMPORARILY_OUTSIDE.value]}
        rows = await HostelResident.find(q).to_list()
        return [
            {
                "resident_id": r.resident_id,
                "student_user_id": str(r.student_user_id),
                "hostel_code": r.hostel_code,
                "building_code": r.building_code,
                "room_code": r.room_code,
                "bed_id": r.bed_id,
                "status": r.status.value,
            }
            for r in rows
        ]

    async def mess_enrollment_report(self, tenant_id: PydanticObjectId, filters: dict) -> list[dict]:
        q: dict = {"tenant_id": tenant_id}
        if filters.get("mess_code"):
            q["mess_code"] = str(filters["mess_code"]).upper()
        rows = await HostelMessEnrollment.find(q).to_list()
        return [
            {
                "enrollment_id": r.enrollment_id,
                "plan_code": r.plan_code,
                "mess_code": r.mess_code,
                "status": r.status.value,
                "rate_snapshot": r.rate_snapshot,
            }
            for r in rows
        ]

    async def mess_billing_outstanding(self, tenant_id: PydanticObjectId, filters: dict) -> list[dict]:
        rows = await HostelMessBillingRecord.find({"tenant_id": tenant_id, "finance_demand_id": {"$ne": None}}).to_list()
        out = []
        for r in rows:
            demand = await StudentFeeDemand.find_one({"tenant_id": tenant_id, "demand_id": r.finance_demand_id})
            if demand is None:
                continue
            if filters.get("only_open") and demand.status == FeeDemandStatus.PAID:
                continue
            out.append(
                {
                    "record_id": r.record_id,
                    "student_user_id": str(r.student_user_id),
                    "amount": r.amount,
                    "finance_demand_id": r.finance_demand_id,
                    "finance_status": demand.status.value,
                }
            )
        return out

    async def visitor_logs(self, tenant_id: PydanticObjectId, filters: dict) -> list[dict]:
        q: dict = {"tenant_id": tenant_id}
        if filters.get("hostel_code"):
            q["hostel_code"] = str(filters["hostel_code"]).upper()
        rows = await HostelVisitorEntry.find(q).sort("-created_at").limit(500).to_list()
        return [
            {
                "visit_id": r.visit_id,
                "visitor_name": r.visitor_name,
                "resident_user_id": str(r.resident_user_id),
                "status": r.status.value,
                "purpose": r.purpose,
            }
            for r in rows
        ]

    async def leave_outpass(self, tenant_id: PydanticObjectId, filters: dict) -> list[dict]:
        leave = await HostelLeaveRequest.find({"tenant_id": tenant_id}).limit(300).to_list()
        outpass = await HostelOutpassRequest.find({"tenant_id": tenant_id}).limit(300).to_list()
        rows = []
        for r in leave:
            rows.append({"kind": "leave", "request_id": r.request_id, "status": r.status.value})
        for r in outpass:
            rows.append({"kind": "outpass", "request_id": r.request_id, "status": r.status.value})
        return rows

    async def maintenance_complaints(self, tenant_id: PydanticObjectId, filters: dict) -> list[dict]:
        q: dict = {"tenant_id": tenant_id}
        if filters.get("category_code"):
            q["category_code"] = str(filters["category_code"]).upper()
        rows = await HostelComplaint.find(q).sort("-created_at").limit(500).to_list()
        return [
            {
                "complaint_id": r.complaint_id,
                "category_code": r.category_code,
                "priority": r.priority.value,
                "status": r.status.value,
                "room_code": r.room_code,
            }
            for r in rows
        ]

    async def rule_acknowledgements(self, tenant_id: PydanticObjectId, filters: dict) -> list[dict]:
        rows = await HostelRuleAcknowledgement.find({"tenant_id": tenant_id}).to_list()
        return [{"rule_code": r.rule_code, "student_user_id": str(r.student_user_id), "rule_version": r.rule_version} for r in rows]

    async def incidents_summary(self, tenant_id: PydanticObjectId, filters: dict) -> list[dict]:
        q: dict = {"tenant_id": tenant_id}
        if not filters.get("include_confidential"):
            q["confidential"] = False
        rows = await HostelIncident.find(q).sort("-created_at").limit(200).to_list()
        return [
            {
                "incident_id": r.incident_id,
                "category": r.category,
                "severity": r.severity.value,
                "status": r.status.value,
                "allegation_only": r.allegation_only,
            }
            for r in rows
        ]

    async def run_report(self, report_key: str, tenant_id: PydanticObjectId, filters: dict) -> list[dict]:
        runners = {
            "occupancy_overview": self.occupancy_overview,
            "applications_summary": self.applications_summary,
            "residents_current": self.residents_current,
            "mess_enrollment": self.mess_enrollment_report,
            "mess_billing_outstanding": self.mess_billing_outstanding,
            "visitor_logs": self.visitor_logs,
            "leave_outpass": self.leave_outpass,
            "maintenance_complaints": self.maintenance_complaints,
            "rule_acknowledgements": self.rule_acknowledgements,
            "incidents_summary": self.incidents_summary,
        }
        fn = runners.get(report_key)
        if fn is None:
            return []
        return await fn(tenant_id, filters)