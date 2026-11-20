import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function LandPlotIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 8L18 5L12 2V12"/>
      <path d="M7.99999 11.9902L2.49999 15.1302C2.34609 15.2175 2.21808 15.3439 2.12902 15.4968C2.03997 15.6496 1.99304 15.8233 1.99304 16.0002C1.99304 16.1771 2.03997 16.3509 2.12902 16.5037C2.21808 16.6565 2.34609 16.783 2.49999 16.8702L11 21.7302C11.304 21.9058 11.6489 21.9982 12 21.9982C12.3511 21.9982 12.696 21.9058 13 21.7302L21.5 16.8702C21.6539 16.783 21.7819 16.6565 21.871 16.5037C21.96 16.3509 22.0069 16.1771 22.0069 16.0002C22.0069 15.8233 21.96 15.6496 21.871 15.4968C21.7819 15.3439 21.6539 15.2175 21.5 15.1302L16 12.0002"/>
      <path d="M6.48999 12.8496L17.51 19.1496"/>
      <path d="M17.51 12.8496L6.5 19.1496"/>

    </svg>
  );
}
