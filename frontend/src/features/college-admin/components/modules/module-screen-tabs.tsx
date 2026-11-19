"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { framesForModule } from "@/features/college-admin/config/frame-registry";
import { cn } from "@/lib/utils";

const MODULE_NUM: Record<string, string> = {
  users: "03",
  organization: "04",
  academics: "05",
  students: "06",
  faculty: "07",
  attendance: "08",
  examinations: "09",
  finance: "10",
  hr: "11",
  library: "12",
  hostel: "13",
  communication: "14",
  lms: "15",
  reports: "16",
  approvals: "17",
  security: "18",
  "data-import": "19",
  integrations: "20",
  helpdesk: "21",
  "finance-extensions": "22",
  operations: "23",
  shared: "24",
};

export function ModuleScreenTabs({ moduleKey }: { moduleKey: string }) {
  const moduleNum = MODULE_NUM[moduleKey];
  if (!moduleNum) return null;
  const frames = framesForModule(moduleNum);
  if (frames.length === 0) return null;
  const pathname = usePathname();

  return (
    <div className="mb-6 border-b border-[#dce3ec]">
      <div className="scrollbar-thin flex gap-3 overflow-x-auto pb-1">
        {frames.map((frame) => {
          const active = pathname === frame.route;
          const label =
            frame.screen === "01"
              ? "Overview"
              : frame.title.length > 28
                ? `${frame.title.slice(0, 26)}…`
                : frame.title;
          return (
            <Link
              key={frame.figmaNodeId}
              href={frame.route}
              data-figma-frame={frame.figmaNodeId}
              className={cn(
                "shrink-0 border-b-2 py-2 text-xs font-medium",
                active
                  ? "border-[#245dd8] text-[#245dd8]"
                  : "border-transparent text-[#607086] hover:text-[#172b45]",
              )}
            >
              {label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}