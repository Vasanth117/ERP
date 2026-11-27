"use client";

import { CommunicationAnnouncementsManagementDashboard } from "@/features/college-admin/components/communication/communication-announcements-management-dashboard";
import {
  CommunicationFacultyNotificationsDashboard,
  CommunicationParentCommunicationDashboard,
  CommunicationStudentNotificationsDashboard,
} from "@/features/college-admin/components/communication/communication-audience-notifications-dashboard";
import {
  CommunicationEmailChannelDashboard,
  CommunicationSmsChannelDashboard,
  CommunicationWhatsappChannelDashboard,
} from "@/features/college-admin/components/communication/communication-channels-dashboard";
import { CommunicationCreateAnnouncementDashboard } from "@/features/college-admin/components/communication/communication-create-announcement-dashboard";
import { CommunicationDashboard } from "@/features/college-admin/components/communication/communication-dashboard";
import {
  CommunicationHistoryDashboard,
  CommunicationDeliveryStatusDashboard,
} from "@/features/college-admin/components/communication/communication-delivery-history-dashboard";
import {
  CommunicationScheduledMessagesDashboard,
  CommunicationTemplatesDashboard,
} from "@/features/college-admin/components/communication/communication-templates-scheduling-dashboard";
import { GenericModuleScreen } from "@/features/college-admin/components/modules/generic-module-screen";
import { resolveModuleEndpoint } from "@/features/college-admin/config/module-endpoint-resolver";

export function CommunicationScreen({ slug, title }: { slug: string; title: string }) {
  const { apiPath, viewType } = resolveModuleEndpoint("communication", slug);
  if (slug === "communication-dashboard") {
    return <CommunicationDashboard />;
  }
  if (slug === "announcements-management") {
    return <CommunicationAnnouncementsManagementDashboard />;
  }
  if (slug === "create-announcement") {
    return <CommunicationCreateAnnouncementDashboard />;
  }
  if (slug === "student-notifications") {
    return <CommunicationStudentNotificationsDashboard />;
  }
  if (slug === "faculty-notifications") {
    return <CommunicationFacultyNotificationsDashboard />;
  }
  if (slug === "parent-communication") {
    return <CommunicationParentCommunicationDashboard />;
  }
  if (slug === "email-communication") {
    return <CommunicationEmailChannelDashboard />;
  }
  if (slug === "sms-communication") {
    return <CommunicationSmsChannelDashboard />;
  }
  if (slug === "whatsapp-communication") {
    return <CommunicationWhatsappChannelDashboard />;
  }
  if (slug === "communication-templates") {
    return <CommunicationTemplatesDashboard />;
  }
  if (slug === "scheduled-messages") {
    return <CommunicationScheduledMessagesDashboard />;
  }
  if (slug === "delivery-status-monitoring") {
    return <CommunicationDeliveryStatusDashboard />;
  }
  if (slug === "communication-history") {
    return <CommunicationHistoryDashboard />;
  }
  return (
    <GenericModuleScreen
      moduleKey="communication"
      slug={slug}
      title={title}
      apiPath={apiPath}
      viewType={viewType}
    />
  );
}