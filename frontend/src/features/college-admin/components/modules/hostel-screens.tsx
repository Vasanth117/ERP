"use client";

import { HostelAdmissionApplicationsDashboard } from "@/features/college-admin/components/hostel/hostel-admission-applications-dashboard";
import { HostelBedAllocationDashboard } from "@/features/college-admin/components/hostel/hostel-bed-allocation-dashboard";
import { HostelBuildingManagementDashboard } from "@/features/college-admin/components/hostel/hostel-building-management-dashboard";
import { HostelDashboard } from "@/features/college-admin/components/hostel/hostel-dashboard";
import { HostelManagementDashboard } from "@/features/college-admin/components/hostel/hostel-management-dashboard";
import { HostelCheckInCheckoutDashboard } from "@/features/college-admin/components/hostel/hostel-check-in-checkout-dashboard";
import { HostelFeeManagementDashboard } from "@/features/college-admin/components/hostel/hostel-fee-management-dashboard";
import { HostelMessManagementDashboard } from "@/features/college-admin/components/hostel/hostel-mess-management-dashboard";
import { HostelLeaveOutpassApprovalDashboard } from "@/features/college-admin/components/hostel/hostel-leave-outpass-approval-dashboard";
import { HostelResidentManagementDashboard } from "@/features/college-admin/components/hostel/hostel-resident-management-dashboard";
import { HostelVisitorManagementDashboard } from "@/features/college-admin/components/hostel/hostel-visitor-management-dashboard";
import { HostelRoomManagementDashboard } from "@/features/college-admin/components/hostel/hostel-room-management-dashboard";
import { HostelReportsDashboard } from "@/features/college-admin/components/hostel/hostel-reports-dashboard";
import { HostelSettingsDashboard } from "@/features/college-admin/components/hostel/hostel-settings-dashboard";

const MANAGEMENT_SLUGS = new Set([
  "maintenance-complaints",
  "hostel-incident-management",
]);

export function HostelScreen({ slug }: { slug: string; title: string }) {
  if (slug === "hostel-dashboard") {
    return <HostelDashboard />;
  }
  if (slug === "hostel-building-management") {
    return <HostelBuildingManagementDashboard />;
  }
  if (slug === "room-management") {
    return <HostelRoomManagementDashboard />;
  }
  if (slug === "hostel-admission-applications") {
    return <HostelAdmissionApplicationsDashboard />;
  }
  if (slug === "bed-allocation") {
    return <HostelBedAllocationDashboard />;
  }
  if (slug === "resident-management") {
    return <HostelResidentManagementDashboard />;
  }
  if (slug === "hostel-check-in-checkout") {
    return <HostelCheckInCheckoutDashboard />;
  }
  if (slug === "hostel-fee-management") {
    return <HostelFeeManagementDashboard />;
  }
  if (slug === "mess-management") {
    return <HostelMessManagementDashboard />;
  }
  if (slug === "visitor-management") {
    return <HostelVisitorManagementDashboard />;
  }
  if (slug === "leave-outpass-approval") {
    return <HostelLeaveOutpassApprovalDashboard />;
  }
  if (slug === "hostel-reports") {
    return <HostelReportsDashboard />;
  }
  if (slug === "hostel-settings") {
    return <HostelSettingsDashboard />;
  }
  if (MANAGEMENT_SLUGS.has(slug)) {
    return <HostelManagementDashboard screenSlug={slug} />;
  }
  return <HostelManagementDashboard screenSlug={slug} />;
}