import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function MouseOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 6V6.343"/>
      <path d="M18.218 18.2182C17.4974 19.612 16.3294 20.7232 14.9015 21.3735C13.4736 22.0239 11.8687 22.1757 10.3442 21.8045C8.81969 21.4334 7.4641 20.5608 6.49496 19.3269C5.52582 18.093 4.99934 16.5692 5 15.0002V9.00023C4.99953 7.88045 5.2677 6.77691 5.782 5.78223"/>
      <path d="M19 13.3431V9.00011C19.0003 7.77708 18.6801 6.57531 18.0714 5.51453C17.4627 4.45374 16.5866 3.57095 15.5306 2.9541C14.4745 2.33724 13.2752 2.00785 12.0522 1.99873C10.8292 1.98961 9.62516 2.30108 8.56 2.90211"/>
      <path d="M22 22L2 2"/>

    </svg>
  );
}
