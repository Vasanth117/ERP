import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CloudAlertIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 12V16"/>
      <path d="M12 20H12.01"/>
      <path d="M17 18.0001H17.5C18.6935 18.0001 19.8381 17.526 20.682 16.6821C21.5259 15.8382 22 14.6936 22 13.5001C22 12.3066 21.5259 11.1621 20.682 10.3181C19.8381 9.47423 18.6935 9.00012 17.5 9.00012H15.71C15.3636 7.8386 14.7216 6.78691 13.8467 5.94801C12.9719 5.10911 11.8942 4.51175 10.7192 4.2144C9.54412 3.91705 8.31202 3.9299 7.14344 4.2517C5.97487 4.57349 4.90988 5.19321 4.05271 6.05017C3.19555 6.90714 2.57559 7.97199 2.25353 9.14049C1.93146 10.309 1.91833 11.5411 2.21541 12.7162C2.51249 13.8913 3.1096 14.9691 3.9483 15.8442C4.787 16.7192 5.83854 17.3615 6.99999 17.7081"/>

    </svg>
  );
}
