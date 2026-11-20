import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MilestoneIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("size-6 shrink-0", className)}
      aria-hidden
      {...props}
    >
      <path d="M12 13V21"/>
      <path d="M12 3V6"/>
      <path d="M4 6C3.73478 6 3.48043 6.10536 3.29289 6.29289C3.10536 6.48043 3 6.73478 3 7V12C3 12.2652 3.10536 12.5196 3.29289 12.7071C3.48043 12.8946 3.73478 13 4 13H17C17.4124 13 17.8148 12.8725 18.152 12.635L21.576 10.318C21.707 10.2257 21.8139 10.1032 21.8877 9.96097C21.9615 9.8187 22.0001 9.66077 22.0001 9.5005C22.0001 9.34022 21.9615 9.1823 21.8877 9.04003C21.8139 8.89775 21.707 8.77531 21.576 8.683L18.152 6.365C17.8148 6.12746 17.4124 5.99997 17 6H4Z"/>

    </svg>
  );
}
