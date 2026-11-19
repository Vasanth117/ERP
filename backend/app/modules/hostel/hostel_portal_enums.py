"""Hostel Admin portal enumerations."""

from enum import Enum


class HostelOperatingStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TEMPORARILY_CLOSED = "temporarily_closed"


class HostelCategory(str, Enum):
    BOYS = "boys"
    GIRLS = "girls"
    MIXED = "mixed"
    INTERNATIONAL = "international"
    STAFF = "staff"
    CUSTOM = "custom"


class HostelBuildingStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class HostelRoomType(str, Enum):
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    FOUR_BED = "four_bed"
    DORMITORY = "dormitory"
    SPECIAL = "special"


class HostelRoomOperationalStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"


class HostelRoomMaintenanceStatus(str, Enum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class HostelFacilityType(str, Enum):
    COMMON_ROOM = "common_room"
    STUDY_ROOM = "study_room"
    RECREATION = "recreation"
    LAUNDRY = "laundry"
    WATER = "water"
    TOILET = "toilet"
    CCTV = "cctv"
    FIRE_SAFETY = "fire_safety"
    MEDICAL = "medical"
    INTERNET = "internet"
    OTHER = "other"


class HostelFacilityCondition(str, Enum):
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNDER_MAINTENANCE = "under_maintenance"


class HostelDashboardDateRange(str, Enum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    SEMESTER = "semester"


class HostelDashboardDrillMetric(str, Enum):
    HOSTELS_ACTIVE = "hostels_active"
    BEDS_AVAILABLE = "beds_available"
    BEDS_OCCUPIED = "beds_occupied"
    RESIDENTS_CHECKED_IN = "residents_checked_in"
    APPLICATIONS_PENDING = "applications_pending"
    WAITING_LIST = "waiting_list"
    VISITORS_INSIDE = "visitors_inside"
    MAINTENANCE_OPEN = "maintenance_open"
    OUTPASS_OVERDUE = "outpass_overdue"
    INCIDENTS_OPEN = "incidents_open"