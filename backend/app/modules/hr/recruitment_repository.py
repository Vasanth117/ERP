"""Recruitment data access (queries and aggregations)."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.modules.hr.enums import HrEmploymentOfferStatus, HrJobOpeningStatus
from app.modules.hr.recruitment_models import (
    HrEmploymentOffer,
    HrJobApplication,
    HrJobOpening,
    HrJobRequisition,
)


class HrRecruitmentRepository:
    async def count_applications(self, tenant_id: PydanticObjectId, **filters) -> int:
        clauses = [Eq(HrJobApplication.tenant_id, tenant_id)]
        if filters.get("department_id"):
            clauses.append(Eq(HrJobApplication.department_id, filters["department_id"]))
        if filters.get("job_opening_id"):
            clauses.append(Eq(HrJobApplication.job_opening_id, filters["job_opening_id"]))
        if filters.get("stage"):
            clauses.append(Eq(HrJobApplication.stage, filters["stage"]))
        return await HrJobApplication.find(*clauses).count()

    async def openings_for_requisition(self, tenant_id: PydanticObjectId, requisition_id: PydanticObjectId) -> list[HrJobOpening]:
        return await HrJobOpening.find(
            Eq(HrJobOpening.tenant_id, tenant_id),
            Eq(HrJobOpening.requisition_id, requisition_id),
        ).to_list()

    async def applications_for_opening(self, tenant_id: PydanticObjectId, opening_id: PydanticObjectId) -> list[HrJobApplication]:
        return await HrJobApplication.find(
            Eq(HrJobApplication.tenant_id, tenant_id),
            Eq(HrJobApplication.job_opening_id, opening_id),
        ).to_list()

    async def department_application_counts(self, tenant_id: PydanticObjectId) -> dict[str, int]:
        rows = await HrJobApplication.find(Eq(HrJobApplication.tenant_id, tenant_id)).to_list()
        counts: dict[str, int] = {}
        for row in rows:
            key = str(row.department_id)
            counts[key] = counts.get(key, 0) + 1
        return counts

    async def opening_performance(self, tenant_id: PydanticObjectId) -> list[dict]:
        openings = await HrJobOpening.find(Eq(HrJobOpening.tenant_id, tenant_id)).to_list()
        report: list[dict] = []
        for opening in openings:
            apps = await self.applications_for_opening(tenant_id, opening.id)
            accepted = sum(1 for a in apps if a.stage.value == "offer_accepted")
            report.append(
                {
                    "opening_id": str(opening.id),
                    "opening_code": opening.opening_code,
                    "status": opening.status.value,
                    "applications": len(apps),
                    "vacancies": opening.vacancies,
                    "filled_count": opening.filled_count,
                    "accepted_offers": accepted,
                }
            )
        return report

    async def time_to_fill_days(self, tenant_id: PydanticObjectId) -> list[dict]:
        openings = await HrJobOpening.find(
            Eq(HrJobOpening.tenant_id, tenant_id),
            Eq(HrJobOpening.status, HrJobOpeningStatus.CLOSED_FILLED),
        ).to_list()
        rows: list[dict] = []
        for opening in openings:
            if not opening.published_at:
                continue
            days = (opening.updated_at.date() - opening.published_at.date()).days
            rows.append({"opening_id": str(opening.id), "opening_code": opening.opening_code, "days_to_fill": max(days, 0)})
        return rows

    async def recruitment_source_breakdown(self, tenant_id: PydanticObjectId) -> dict[str, int]:
        apps = await HrJobApplication.find(Eq(HrJobApplication.tenant_id, tenant_id)).to_list()
        out: dict[str, int] = {}
        for app in apps:
            out[app.application_source] = out.get(app.application_source, 0) + 1
        return out

    async def requisition_progress(self, tenant_id: PydanticObjectId, requisition_id: PydanticObjectId) -> dict:
        req = await HrJobRequisition.get(requisition_id)
        if req is None or req.tenant_id != tenant_id:
            return {}
        openings = await self.openings_for_requisition(tenant_id, requisition_id)
        opening_ids = {o.id for o in openings}
        application_total = sum(await self.count_applications(tenant_id, job_opening_id=o.id) for o in openings)
        offer_count = 0
        offer_accepted = 0
        offers = await HrEmploymentOffer.find(Eq(HrEmploymentOffer.tenant_id, tenant_id)).to_list()
        for offer in offers:
            if offer.job_opening_id not in opening_ids:
                continue
            offer_count += 1
            if offer.status == HrEmploymentOfferStatus.ACCEPTED:
                offer_accepted += 1
        filled = sum(o.filled_count for o in openings)
        return {
            "requisition_id": str(requisition_id),
            "status": req.status.value,
            "openings_count": len(openings),
            "applications_count": application_total,
            "offers_count": offer_count,
            "offers_accepted": offer_accepted,
            "positions_filled": filled,
            "positions_required": req.positions_required,
        }