import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function FishIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M6.5 12C7.44 8.54 11.44 6 15 6C18.56 6 21.06 8.54 22 12C21.06 15.47 18.56 18 15 18C11.44 18 7.44 15.47 6.5 12Z"/>
      <path d="M18 12V12.5"/>
      <path d="M16 17.9303C14.6992 16.2271 13.9945 14.1434 13.9945 12.0003C13.9945 9.85719 14.6992 7.77352 16 6.07031"/>
      <path d="M7.00001 10.67C7.00001 8 5.58001 5.97 2.73001 5.5C1.73001 7 1.73001 10.5 2.96001 12C1.72001 13.5 1.72001 17 2.73001 18.5C5.58001 18.03 7.00001 16 7.00001 13.33"/>
      <path d="M10.46 7.26001C10.2 5.88001 9.17 4.24001 8 3.00001H13.8C14.2745 2.99826 14.7342 3.16526 15.0969 3.47118C15.4596 3.7771 15.7017 4.20202 15.78 4.67001L16.01 6.07001"/>
      <path d="M16.01 17.9295L15.78 19.3295C15.7017 19.7975 15.4596 20.2224 15.0969 20.5284C14.7342 20.8343 14.2745 21.0013 13.8 20.9995H9.5C10.4689 19.901 10.9993 18.4842 10.99 17.0195"/>

    </svg>
  );
}
