import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CirclePowerIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 7V11"/>
      <path d="M7.99801 9.00305C7.44133 9.74624 7.10262 10.6298 7.0198 11.5546C6.93699 12.4795 7.11336 13.4091 7.52914 14.2394C7.94493 15.0697 8.5837 15.7678 9.37388 16.2554C10.1641 16.7431 11.0744 17.0011 12.003 17.0005C12.9316 17 13.8416 16.7408 14.6312 16.2522C15.4208 15.7635 16.0587 15.0646 16.4734 14.2338C16.8882 13.403 17.0634 12.4732 16.9794 11.5484C16.8954 10.6237 16.5556 9.74055 15.998 8.99805"/>
      <path d="M2 12C2 14.6522 3.05357 17.1957 4.92893 19.0711C6.8043 20.9464 9.34784 22 12 22C14.6522 22 17.1957 20.9464 19.0711 19.0711C20.9464 17.1957 22 14.6522 22 12C22 9.34784 20.9464 6.8043 19.0711 4.92893C17.1957 3.05357 14.6522 2 12 2C9.34784 2 6.8043 3.05357 4.92893 4.92893C3.05357 6.8043 2 9.34784 2 12Z"/>

    </svg>
  );
}
