import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PowerIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 2V12"/>
      <path d="M18.4 6.59961C19.6567 7.85672 20.513 9.45778 20.8609 11.2009C21.2087 12.944 21.0327 14.7511 20.3549 16.3943C19.6771 18.0375 18.5279 19.4432 17.0523 20.4341C15.5766 21.425 13.8406 21.9568 12.0631 21.9624C10.2856 21.9679 8.5463 21.447 7.06447 20.4654C5.58264 19.4837 4.42467 18.0853 3.7366 16.4463C3.04852 14.8074 2.86115 13.0015 3.19812 11.2562C3.53509 9.51096 4.3813 7.90456 5.63005 6.63961"/>

    </svg>
  );
}
