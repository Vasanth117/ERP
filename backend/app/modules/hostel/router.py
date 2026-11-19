"""Hostel Admin module — dashboard and infrastructure (phase 1)."""

from fastapi import APIRouter

from app.modules.hostel.allocation_router import router as allocation_router
from app.modules.hostel.application_router import router as application_router
from app.modules.hostel.dashboard_router import router as dashboard_router
from app.modules.hostel.infrastructure_router import router as infrastructure_router
from app.modules.hostel.resident_router import router as resident_router
from app.modules.hostel.leave_outpass_router import router as leave_outpass_router
from app.modules.hostel.communication_router import router as communication_router
from app.modules.hostel.maintenance_router import router as maintenance_router
from app.modules.hostel.reports_router import router as reports_router
from app.modules.hostel.mess_router import router as mess_router
from app.modules.hostel.rules_incident_router import router as rules_incident_router
from app.modules.hostel.visitor_router import router as visitor_router
from app.modules.hostel.integration_router import router as integration_router
from app.modules.hostel.audit_config_router import router as audit_config_router

router = APIRouter()
router.include_router(dashboard_router)
router.include_router(infrastructure_router)
router.include_router(allocation_router)
router.include_router(application_router)
router.include_router(resident_router)
router.include_router(visitor_router)
router.include_router(mess_router)
router.include_router(leave_outpass_router)
router.include_router(maintenance_router)
router.include_router(rules_incident_router)
router.include_router(communication_router)
router.include_router(reports_router)
router.include_router(integration_router)
router.include_router(audit_config_router)