import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function RulerIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <g clip-path="url(#clip0_355_914)">
      <path d="M21.3 15.3C21.5237 15.523 21.7013 15.788 21.8224 16.0797C21.9435 16.3714 22.0059 16.6842 22.0059 17C22.0059 17.3159 21.9435 17.6287 21.8224 17.9204C21.7013 18.2121 21.5237 18.4771 21.3 18.7L18.7 21.3C18.477 21.5238 18.2121 21.7013 17.9203 21.8225C17.6286 21.9436 17.3159 22.0059 17 22.0059C16.6841 22.0059 16.3713 21.9436 16.0796 21.8225C15.7879 21.7013 15.523 21.5238 15.3 21.3L2.69999 8.70005C2.25054 8.24842 1.99823 7.6372 1.99823 7.00005C1.99823 6.36289 2.25054 5.75167 2.69999 5.30005L5.29999 2.70005C5.75161 2.2506 6.36283 1.99829 6.99999 1.99829C7.63714 1.99829 8.24836 2.2506 8.69999 2.70005L21.3 15.3Z"/>
      <path d="M14.5 12.5L16.5 10.5"/>
      <path d="M11.5 9.5L13.5 7.5"/>
      <path d="M8.5 6.5L10.5 4.5"/>
      <path d="M17.5 15.5L19.5 13.5"/>
      </g>
      <defs>
      <clipPath id="clip0_355_914">
      <rect width="24" height="24"/>
      </clipPath>
      </defs>

    </svg>
  );
}
