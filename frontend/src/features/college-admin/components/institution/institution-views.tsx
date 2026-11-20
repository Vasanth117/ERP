"use client";

import Link from "next/link";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeading } from "@/features/college-admin/components/layout/page-heading";
import {
  QueryState,
  StatCard,
} from "@/features/college-admin/components/ui/query-state";
import {
  useCampuses,
  useCreateCampus,
  useInstitutionSettings,
  useUpdateCampus,
  useUpdateInstitutionSettings,
} from "@/features/college-admin/hooks/use-institution";
import { InstitutionBrandingForm } from "@/features/college-admin/components/institution/institution-branding-form";
import { InstitutionInformationForm } from "@/features/college-admin/components/institution/institution-information-form";
import { AcademicInstitutionSettingsForm } from "@/features/college-admin/components/institution/academic-institution-settings-form";
import { AcademicYearConfigurationDashboard } from "@/features/college-admin/components/institution/academic-year-configuration-dashboard";
import { InstitutionalCalendarSettingsDashboard } from "@/features/college-admin/components/institution/institutional-calendar-settings-dashboard";
import { ConfigurationHistoryDashboard } from "@/features/college-admin/components/institution/configuration-history-dashboard";
import { InstitutionalPoliciesDashboard } from "@/features/college-admin/components/institution/institutional-policies-dashboard";
import { CampusContactForm } from "@/features/college-admin/components/institution/campus-contact-form";
import { CampusDetailDashboard } from "@/features/college-admin/components/institution/campus-detail-dashboard";
import { CampusManagementDashboard } from "@/features/college-admin/components/institution/campus-management-dashboard";
import { InstitutionProfileDashboard } from "@/features/college-admin/components/institution/institution-profile-dashboard";
import type { InstitutionProfile } from "@/features/college-admin/types/institution";

export function InstitutionProfileView() {
  return <InstitutionProfileDashboard />;
}

export function InstitutionInformationView() {
  return <InstitutionInformationForm />;
}

export function InstitutionBrandingView() {
  return <InstitutionBrandingForm />;
}

export function CampusesDashboardView() {
  return <CampusManagementDashboard />;
}

export function CampusDetailView({ campusId }: { campusId: string }) {
  return <CampusDetailDashboard campusId={campusId} />;
}

export function CampusContactView({ campusId }: { campusId: string }) {
  return <CampusContactForm campusId={campusId} />;
}

export function AcademicSettingsView() {
  return <AcademicInstitutionSettingsForm />;
}

export function InstitutionPoliciesView() {
  return <InstitutionalPoliciesDashboard />;
}

export function AcademicYearView() {
  return <AcademicYearConfigurationDashboard />;
}

export function CalendarSettingsView() {
  return <InstitutionalCalendarSettingsDashboard />;
}

export function ConfigurationHistoryView() {
  return <ConfigurationHistoryDashboard />;
}

function ProfileField({
  label,
  id,
  register,
}: {
  label: string;
  id: keyof InstitutionProfile;
  register: ReturnType<typeof useForm<Partial<InstitutionProfile>>>["register"];
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} {...register(id)} className="border-[#dce3ec]" />
    </div>
  );
}

function Field({
  label,
  name,
  defaultValue,
}: {
  label: string;
  name: string;
  defaultValue?: string;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={name}>{label}</Label>
      <Input
        id={name}
        name={name}
        defaultValue={defaultValue}
        className="border-[#dce3ec]"
      />
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="rounded-lg border border-[#dce3ec] bg-white p-4">
      <dt className="text-[11px] font-semibold uppercase text-[#8a98aa]">
        {label}
      </dt>
      <dd className="mt-1 text-sm text-[#172b45]">{value ?? "—"}</dd>
    </div>
  );
}