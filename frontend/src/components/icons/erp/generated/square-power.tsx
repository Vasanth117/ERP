import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function SquarePowerIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3Z"/>

    </svg>
  );
}
