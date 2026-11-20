import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CloudLightningIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6 16.3263C4.94623 15.8259 4.03422 15.0701 3.34686 14.1276C2.6595 13.1851 2.21858 12.0857 2.06418 10.9294C1.90978 9.77315 2.0468 8.59662 2.46278 7.50678C2.87876 6.41693 3.56051 5.44832 4.44606 4.68898C5.33162 3.92965 6.39291 3.40366 7.53346 3.15883C8.67402 2.91401 9.85768 2.9581 10.9769 3.2871C12.096 3.61611 13.1152 4.2196 13.9419 5.04271C14.7685 5.86583 15.3763 6.88248 15.71 8.00025H17.5C18.6515 7.99824 19.7599 8.43773 20.5972 9.22825C21.4345 10.0188 21.9368 11.1002 22.0009 12.2499C22.0649 13.3996 21.6858 14.5301 20.9416 15.4088C20.1973 16.2874 19.1446 16.8473 18 16.9733"/>
      <path d="M13 12L10 17H14L11 22"/>

    </svg>
  );
}
