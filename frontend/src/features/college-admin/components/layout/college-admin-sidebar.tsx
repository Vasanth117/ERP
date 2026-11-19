"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import { collegeAdminNavGroups } from "@/features/college-admin/config/navigation";
import { useInstitutionProfile } from "@/features/college-admin/hooks/use-institution";
import { cn } from "@/lib/utils";

function navActive(pathname: string, href: string): boolean {
  if (href === "/college-admin/dashboard") {
    return pathname === href || pathname.startsWith(`${href}/`);
  }
  if (href.startsWith("/college-admin/institution")) {
    return pathname.startsWith("/college-admin/institution");
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function CollegeAdminSidebar() {
  const pathname = usePathname();
  const { data: profile } = useInstitutionProfile();

  const displayName = profile?.display_name ?? "Institution";
  const tenantCode = profile?.tenant_code ?? "—";

  return (
    <aside
      className="flex w-[264px] shrink-0 flex-col gap-4 border-r border-[#dce3ec] bg-white p-4"
      data-figma-node="64:163"
    >
      <div className="flex items-center gap-2.5">
        <CollegeAdminIcon name="a5ede" size={24} />
        <div className="leading-tight">
          <p className="text-[11px] font-bold text-[#172b45]">COLLEGE ERP</p>
          <p className="text-[11px] text-[#607086]">College Admin</p>
        </div>
      </div>

      <div className="flex items-center justify-between rounded-md border border-[#dce3ec] px-2.5 py-2">
        <div className="min-w-0">
          <p className="truncate text-xs font-semibold text-[#172b45]">
            {displayName}
          </p>
          <p className="truncate text-[10px] text-[#607086]">
            Tenant {tenantCode} · Main campus
          </p>
        </div>
        <CollegeAdminIcon name="c5ad3" size={14} />
      </div>

      <nav className="flex flex-1 flex-col gap-4 overflow-y-auto">
        {collegeAdminNavGroups.map((group) => (
          <div key={group.title}>
            <p className="text-[10px] font-semibold text-[#8a98aa]">
              {group.title}
            </p>
            <ul className="mt-1.5 flex flex-col gap-0.5 pt-1">
              {group.items.map((item) => {
                const active = navActive(pathname, item.href);
                return (
                  <li key={item.id}>
                    <Link
                      href={item.href}
                      className={cn(
                        "flex h-8 items-center gap-2.5 rounded-md px-2.5 text-xs transition-colors",
                        active
                          ? "bg-[#ebf2ff] font-medium text-[#245dd8]"
                          : "text-[#172b45] hover:bg-[#f5f8ff]",
                      )}
                    >
                      <CollegeAdminIcon name={item.icon} />
                      <span className="truncate">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <p className="text-[10px] text-[#8a98aa]">
        College Admin v1.0 · Illustrative environment
      </p>
      <Link
        href="/"
        className="text-[11px] font-medium text-[#245dd8] hover:underline"
      >
        ← Main module launcher
      </Link>
    </aside>
  );
}