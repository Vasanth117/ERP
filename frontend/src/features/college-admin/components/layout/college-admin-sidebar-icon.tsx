import type { ErpIconName } from "@/components/icons/erp/names";
import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import { cn } from "@/lib/utils";

export function CollegeAdminSidebarIcon({
  name,
  size = 20,
  active = false,
  className,
}: {
  name: ErpIconName | string;
  size?: number;
  active?: boolean;
  className?: string;
}) {
  const tone = cn(
    "shrink-0",
    active ? "text-[#245dd8]" : "text-[#636e7b]",
    className,
  );

  return <CollegeAdminIcon name={name} size={size} className={tone} />;
}