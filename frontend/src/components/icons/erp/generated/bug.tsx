import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function BugIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M8 2L9.88 3.88"/>
      <path d="M14.12 3.88L16 2"/>
      <path d="M9.00001 7.12987V6.12987C8.98188 5.72462 9.04605 5.3199 9.18864 4.94012C9.33123 4.56035 9.54928 4.21341 9.82964 3.92022C10.11 3.62704 10.4469 3.3937 10.8199 3.23428C11.1929 3.07486 11.5944 2.99268 12 2.99268C12.4057 2.99268 12.8071 3.07486 13.1801 3.23428C13.5532 3.3937 13.89 3.62704 14.1704 3.92022C14.4507 4.21341 14.6688 4.56035 14.8114 4.94012C14.954 5.3199 15.0181 5.72462 15 6.12987V7.12987"/>
      <path d="M12 20C8.7 20 6 17.3 6 14V11C6 9.93913 6.42143 8.92172 7.17157 8.17157C7.92172 7.42143 8.93913 7 10 7H14C15.0609 7 16.0783 7.42143 16.8284 8.17157C17.5786 8.92172 18 9.93913 18 11V14C18 17.3 15.3 20 12 20Z"/>
      <path d="M12 20V11"/>
      <path d="M6.53 9C4.6 8.8 3 7.1 3 5"/>
      <path d="M6 13H2"/>
      <path d="M3 21C3 18.9 4.7 17.1 6.8 17"/>
      <path d="M20.97 5C20.97 7.1 19.37 8.8 17.47 9"/>
      <path d="M22 13H18"/>
      <path d="M17.2 17C19.3 17.1 21 18.9 21 21"/>

    </svg>
  );
}
