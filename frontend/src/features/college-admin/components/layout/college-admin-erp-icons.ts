import type { ComponentType, SVGProps } from "react";

import type { ErpIconName } from "@/components/icons/erp/names";
import { BackendLogoIcon } from "@/components/icons/erp/generated/backend-logo";
import { BenchlogoNameIcon } from "@/components/icons/erp/generated/benchlogo_name";
import { BellIcon } from "@/components/icons/erp/generated/bell";
import { BookOpenIcon } from "@/components/icons/erp/generated/book-open";
import { Building2Icon } from "@/components/icons/erp/generated/building-2";
import { ContactIcon } from "@/components/icons/erp/generated/contact";
import { CalendarCheckIcon } from "@/components/icons/erp/generated/calendar-check";
import { ChartBarIcon } from "@/components/icons/erp/generated/chart-bar";
import { ChevronDownIcon } from "@/components/icons/erp/generated/chevron-down";
import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { CircleIcon } from "@/components/icons/erp/generated/circle";
import { ClipboardListIcon } from "@/components/icons/erp/generated/clipboard-list";
import { DatabaseIcon } from "@/components/icons/erp/generated/database";
import { DownloadIcon } from "@/components/icons/erp/generated/download";
import { GraduationCapIcon } from "@/components/icons/erp/generated/graduation-cap";
import { HotelIcon } from "@/components/icons/erp/generated/hotel";
import { IdCardIcon } from "@/components/icons/erp/generated/id-card";
import { LandmarkIcon } from "@/components/icons/erp/generated/landmark";
import { LayoutDashboardIcon } from "@/components/icons/erp/generated/layout-dashboard";
import { LayoutGridIcon } from "@/components/icons/erp/generated/layout-grid";
import { LibraryBigIcon } from "@/components/icons/erp/generated/library-big";
import { LifeBuoyIcon } from "@/components/icons/erp/generated/life-buoy";
import { MegaphoneIcon } from "@/components/icons/erp/generated/megaphone";
import { MessageSquareIcon } from "@/components/icons/erp/generated/message-square";
import { MonitorPlayIcon } from "@/components/icons/erp/generated/monitor-play";
import { NetworkIcon } from "@/components/icons/erp/generated/network";
import { PanelsTopLeftIcon } from "@/components/icons/erp/generated/panels-top-left";
import { PlugIcon } from "@/components/icons/erp/generated/plug";
import { ReceiptIcon } from "@/components/icons/erp/generated/receipt";
import { RefreshCwIcon } from "@/components/icons/erp/generated/refresh-cw";
import { SearchIcon } from "@/components/icons/erp/generated/search";
import { Settings2Icon } from "@/components/icons/erp/generated/settings-2";
import { SchoolIcon } from "@/components/icons/erp/generated/school";
import { ShieldCheckIcon } from "@/components/icons/erp/generated/shield-check";
import { ShieldIcon } from "@/components/icons/erp/generated/shield";
import { SlidersHorizontalIcon } from "@/components/icons/erp/generated/sliders-horizontal";
import { SquareCheckIcon } from "@/components/icons/erp/generated/square-check";
import { UserCogIcon } from "@/components/icons/erp/generated/user-cog";
import { UserRoundCogIcon } from "@/components/icons/erp/generated/user-round-cog";
import { UsersIcon } from "@/components/icons/erp/generated/users";
import { WalletIcon } from "@/components/icons/erp/generated/wallet";
import { WorkflowIcon } from "@/components/icons/erp/generated/workflow";
import { WrenchIcon } from "@/components/icons/erp/generated/wrench";

type ErpIconComponent = ComponentType<SVGProps<SVGSVGElement>>;

/** Figma / legacy `public/college-admin/icons/<id>.svg` ids → ERP Lucide slug. */
export const COLLEGE_ADMIN_LEGACY_ICON_SLUG: Record<string, ErpIconName> = {
  "3e5bc": "layout-grid",
  de8b2: "building-2",
  c9306: "users",
  "181e9": "network",
  f5b42: "book-open",
  eb36a: "graduation-cap",
  "629af": "id-card",
  a1df0: "calendar-check",
  "48683": "clipboard-list",
  e15fc: "monitor-play",
  f21fe: "wallet",
  "53516": "users",
  "812ba": "library-big",
  a4dde: "building-2",
  da97a: "message-square",
  a8dc1: "chart-bar",
  ee32f: "square-check",
  a75fd: "shield",
  "46882": "database",
  "495b3": "plug",
  "09b1d": "life-buoy",
  "1433e": "receipt",
  bcb49: "settings-2",
  c5ad3: "workflow",
  a5ede: "layout-grid",
  "h-738bc": "search",
  "h-ca0a6": "bell",
  "h-4038e": "chevron-down",
  "h-a05cf": "circle",
  "h-404d1": "circle",
};

const ERP_ICON_COMPONENTS: Partial<Record<ErpIconName, ErpIconComponent>> = {
  "backend-logo": BackendLogoIcon,
  "benchlogo_name": BenchlogoNameIcon,
  "layout-grid": LayoutGridIcon,
  "layout-dashboard": LayoutDashboardIcon,
  "panels-top-left": PanelsTopLeftIcon,
  "building-2": Building2Icon,
  users: UsersIcon,
  network: NetworkIcon,
  "book-open": BookOpenIcon,
  "graduation-cap": GraduationCapIcon,
  "id-card": IdCardIcon,
  "calendar-check": CalendarCheckIcon,
  "clipboard-list": ClipboardListIcon,
  "monitor-play": MonitorPlayIcon,
  wallet: WalletIcon,
  "library-big": LibraryBigIcon,
  "message-square": MessageSquareIcon,
  "chart-bar": ChartBarIcon,
  "square-check": SquareCheckIcon,
  shield: ShieldIcon,
  database: DatabaseIcon,
  plug: PlugIcon,
  "life-buoy": LifeBuoyIcon,
  receipt: ReceiptIcon,
  "settings-2": Settings2Icon,
  workflow: WorkflowIcon,
  search: SearchIcon,
  bell: BellIcon,
  "chevron-down": ChevronDownIcon,
  "chevron-left": ChevronLeftIcon,
  "chevron-right": ChevronRightIcon,
  circle: CircleIcon,
  download: DownloadIcon,
  megaphone: MegaphoneIcon,
  "refresh-cw": RefreshCwIcon,
  contact: ContactIcon,
  hotel: HotelIcon,
  landmark: LandmarkIcon,
  school: SchoolIcon,
  "shield-check": ShieldCheckIcon,
  "sliders-horizontal": SlidersHorizontalIcon,
  "user-cog": UserCogIcon,
  "user-round-cog": UserRoundCogIcon,
  wrench: WrenchIcon,
};

const FALLBACK_SLUG: ErpIconName = "layout-grid";

export function resolveCollegeAdminIconSlug(name: string): ErpIconName {
  const mapped = COLLEGE_ADMIN_LEGACY_ICON_SLUG[name];
  if (mapped) return mapped;
  if (name in ERP_ICON_COMPONENTS) return name as ErpIconName;
  if (/^[a-z][a-z0-9_-]*$/.test(name)) return name as ErpIconName;
  return FALLBACK_SLUG;
}

export function getCollegeAdminErpIcon(
  slug: ErpIconName,
): ErpIconComponent | undefined {
  return ERP_ICON_COMPONENTS[slug];
}

export const CollegeAdminChevronLeft = ChevronLeftIcon;
export const CollegeAdminChevronRight = ChevronRightIcon;
export const CollegeAdminChevronDown = ChevronDownIcon;
export const CollegeAdminDownload = DownloadIcon;
export const CollegeAdminMegaphone = MegaphoneIcon;
export const CollegeAdminRefreshCw = RefreshCwIcon;