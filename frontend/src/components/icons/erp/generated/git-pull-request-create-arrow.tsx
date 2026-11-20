import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function GitPullRequestCreateArrowIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M2 6C2 6.79565 2.31607 7.55871 2.87868 8.12132C3.44129 8.68393 4.20435 9 5 9C5.79565 9 6.55871 8.68393 7.12132 8.12132C7.68393 7.55871 8 6.79565 8 6C8 5.20435 7.68393 4.44129 7.12132 3.87868C6.55871 3.31607 5.79565 3 5 3C4.20435 3 3.44129 3.31607 2.87868 3.87868C2.31607 4.44129 2 5.20435 2 6Z"/>
      <path d="M5 9V21"/>
      <path d="M15 9L12 6L15 3"/>
      <path d="M12 6H17C17.5304 6 18.0391 6.21071 18.4142 6.58579C18.7893 6.96086 19 7.46957 19 8V11"/>
      <path d="M19 15V21"/>
      <path d="M22 18H16"/>

    </svg>
  );
}
