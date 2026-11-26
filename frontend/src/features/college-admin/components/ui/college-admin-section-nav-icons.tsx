import type { ComponentType, SVGProps } from "react";

import { BanIcon } from "@/components/icons/erp/generated/ban";
import { BookOpenIcon } from "@/components/icons/erp/generated/book-open";
import { CalendarCheckIcon } from "@/components/icons/erp/generated/calendar-check";
import { CalendarDaysIcon } from "@/components/icons/erp/generated/calendar-days";
import { ChartBarIcon } from "@/components/icons/erp/generated/chart-bar";
import { CircleCheckIcon } from "@/components/icons/erp/generated/circle-check";
import { ClipboardListIcon } from "@/components/icons/erp/generated/clipboard-list";
import { CoinsIcon } from "@/components/icons/erp/generated/coins";
import { FilePenLineIcon } from "@/components/icons/erp/generated/file-pen-line";
import { GitBranchIcon } from "@/components/icons/erp/generated/git-branch";
import { GraduationCapIcon } from "@/components/icons/erp/generated/graduation-cap";
import { HotelIcon } from "@/components/icons/erp/generated/hotel";
import { IdCardIcon } from "@/components/icons/erp/generated/id-card";
import { LayersIcon } from "@/components/icons/erp/generated/layers";
import { LayoutGridIcon } from "@/components/icons/erp/generated/layout-grid";
import { ListIcon } from "@/components/icons/erp/generated/list";
import { ListChecksIcon } from "@/components/icons/erp/generated/list-checks";
import { RefreshCwIcon } from "@/components/icons/erp/generated/refresh-cw";
import { SendIcon } from "@/components/icons/erp/generated/send";
import { Settings2Icon } from "@/components/icons/erp/generated/settings-2";
import { UserCheckIcon } from "@/components/icons/erp/generated/user-check";
import { UsersIcon } from "@/components/icons/erp/generated/users";
import { CircleIcon } from "@/components/icons/erp/generated/circle";
import { DatabaseIcon } from "@/components/icons/erp/generated/database";
import { MailIcon } from "@/components/icons/erp/generated/mail";

type NavIcon = ComponentType<SVGProps<SVGSVGElement>>;

const SECTION_NAV_ICONS: Record<string, NavIcon> = {
  years: CalendarDaysIcon,
  semesters: LayersIcon,
  calendar: CalendarCheckIcon,
  course_configuration: Settings2Icon,
  curriculum: GitBranchIcon,
  subjects: BookOpenIcon,
  credit: CoinsIcon,
  grading: GraduationCapIcon,
  registrations: ClipboardListIcon,
  eligibility: UserCheckIcon,
  hall_tickets: IdCardIcon,
  seating: HotelIcon,
  invigilation: UsersIcon,
  marks_entry: FilePenLineIcon,
  assessment: ListChecksIcon,
  processing: ChartBarIcon,
  approval: CircleCheckIcon,
  publication: SendIcon,
  revaluation: RefreshCwIcon,
  supplementary: GraduationCapIcon,
  list: ListIcon,
  month: CalendarDaysIcon,
  semester: LayoutGridIcon,
  suspended: BanIcon,
  pending_activation: MailIcon,
  deactivated: DatabaseIcon,
  online: RefreshCwIcon,
  offline: CoinsIcon,
  all: ListIcon,
  receipts: ClipboardListIcon,
  dues: ChartBarIcon,
  scholarships: GraduationCapIcon,
  concessions: CoinsIcon,
  refunds: RefreshCwIcon,
  reconciliation: RefreshCwIcon,
  reports: ChartBarIcon,
  branches: GitBranchIcon,
  catalogue: BookOpenIcon,
  inventory: DatabaseIcon,
  acquisition: ClipboardListIcon,
  issue_return: RefreshCwIcon,
  reservations: ListChecksIcon,
  members: UsersIcon,
  fines: CoinsIcon,
  lost_damaged: BanIcon,
  summary: ChartBarIcon,
  settings: Settings2Icon,
  buildings: HotelIcon,
  rooms: LayoutGridIcon,
  bed_allocation: LayersIcon,
  applications: ClipboardListIcon,
  residents: UsersIcon,
  check_in: UserCheckIcon,
  fees: CoinsIcon,
  mess: ClipboardListIcon,
  visitors: IdCardIcon,
  outpass: SendIcon,
  maintenance: RefreshCwIcon,
  incidents: BanIcon,
};

function resolveNavIcon(navKey: string): NavIcon {
  if (/^\d+$/.test(navKey)) {
    return LayersIcon;
  }
  return SECTION_NAV_ICONS[navKey] ?? CircleIcon;
}

export function CollegeAdminSectionNavIcon({
  navKey,
  className,
}: {
  navKey: string;
  className?: string;
}) {
  const Icon = resolveNavIcon(navKey);
  return <Icon className={className} aria-hidden />;
}