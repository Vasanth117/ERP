import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function ClockAlertIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 6V12L16 14"/>
      <path d="M16 21.1598C14.2026 21.9451 12.2139 22.1843 10.2815 21.8479C8.34914 21.5115 6.55836 20.6142 5.13208 19.2677C3.70579 17.9212 2.70698 16.185 2.25995 14.2752C1.81292 12.3653 1.93742 10.3662 2.61796 8.52657C3.29849 6.68696 4.505 5.08809 6.08733 3.92898C7.66966 2.76987 9.55793 2.10169 11.5171 2.00761C13.4763 1.91352 15.4199 2.39769 17.106 3.39985C18.7922 4.40201 20.1463 5.8779 21 7.64384"/>
      <path d="M20 11.5V17.5"/>
      <path d="M20 21.5H20.01"/>

    </svg>
  );
}
