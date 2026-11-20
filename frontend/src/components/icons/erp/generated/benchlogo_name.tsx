import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

/** Wordmark: “benchend”. Source: `benchlogo_name.svg`. */
export function BenchlogoNameIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="207.703 124 384.583 84"
      fill="none"
      role="img"
      className={cn("h-auto w-auto shrink-0", className)}
      aria-label="benchend"
      {...props}
    >
      <text
        fill="#1B2430"
        fontFamily="'Space Grotesk', Inter, system-ui, sans-serif"
        fontSize="84"
        fontWeight="700"
        letterSpacing="-3"
        dominantBaseline="text-after-edge"
      >
        <tspan x="207.703" y="219.133">
          benchend
        </tspan>
      </text>
    </svg>
  );
}