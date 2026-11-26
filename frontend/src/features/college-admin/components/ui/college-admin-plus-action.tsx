import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { cn } from "@/lib/utils";

import { collegeAdminActionLabel } from "@/features/college-admin/components/ui/college-admin-page-buttons";

/** Icon + text for primary “add/create” actions; strips a leading "+" from API labels. */
export function CollegeAdminPlusActionLabel({
  label,
  iconClassName = "size-3.5",
}: {
  label?: string;
  iconClassName?: string;
}) {
  return (
    <>
      <PlusIcon className={cn(iconClassName, "shrink-0")} aria-hidden />
      {collegeAdminActionLabel(label)}
    </>
  );
}