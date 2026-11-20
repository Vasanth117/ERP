import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FileHeartIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M4 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V7L15 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V6"/>
      <path d="M14 2V6C14 6.53043 14.2107 7.03914 14.5858 7.41421C14.9609 7.78929 15.4696 8 16 8H20"/>
      <path d="M10.29 10.6999C9.94839 10.3589 9.51296 10.1273 9.03921 10.0346C8.56546 9.94203 8.07486 9.99262 7.62998 10.1799C7.33998 10.2999 7.06998 10.4799 6.84998 10.7099L6.49998 11.0499L6.14998 10.7099C5.81035 10.3692 5.37721 10.1369 4.90545 10.0426C4.43369 9.94823 3.94454 9.99604 3.49998 10.1799C3.19998 10.2999 2.93998 10.4799 2.70998 10.7099C1.75998 11.6499 1.70998 13.2399 2.90998 14.4499L6.49998 17.9999L10.1 14.4499C11.3 13.2399 11.24 11.6499 10.29 10.7099V10.6999Z"/>

    </svg>
  );
}
