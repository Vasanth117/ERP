import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

/** Wordmark: “benchend”. Source: `benchlogo_name.svg`. */
const VIEWBOX_W = 118;
const VIEWBOX_H = 20;
const DEFAULT_WIDTH = 154;
const DEFAULT_HEIGHT = 27;

export function BenchlogoNameIcon({
  className,
  width = DEFAULT_WIDTH,
  height = DEFAULT_HEIGHT,
  ...props
}: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={`0 0 ${VIEWBOX_W} ${VIEWBOX_H}`}
      width={width}
      height={height}
      fill="none"
      role="img"
      className={cn("block max-w-full shrink-0", className)}
      aria-label="benchend"
      preserveAspectRatio="xMinYMid meet"
      {...props}
    >
      <text
        fill="#1B2430"
        fontFamily="'Space Grotesk', Inter, system-ui, sans-serif"
        fontSize="17"
        fontWeight="700"
        letterSpacing="-0.55"
        dominantBaseline="alphabetic"
        x="0"
        y="16.5"
      >
        benchend
      </text>
    </svg>
  );
}