import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function HeadphoneOffIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21 14H19.657"/>
      <path d="M9.128 3.46957C10.4817 3.01374 11.9245 2.88669 13.3371 3.09891C14.7497 3.31112 16.0915 3.85652 17.2515 4.69001C18.4115 5.5235 19.3565 6.62113 20.0084 7.89217C20.6602 9.16321 21.0001 10.5711 21 11.9996V15.3426"/>
      <path d="M2 2L22 22"/>
      <path d="M20.414 20.414C20.039 20.7891 19.5304 20.9999 19 21H18C17.4696 21 16.9609 20.7893 16.5858 20.4142C16.2107 20.0391 16 19.5304 16 19V16"/>
      <path d="M3 13.9997H6C6.53043 13.9997 7.03914 14.2105 7.41421 14.5855C7.78929 14.9606 8 15.4693 8 15.9997V18.9997C8 19.5302 7.78929 20.0389 7.41421 20.414C7.03914 20.789 6.53043 20.9997 6 20.9997H5C4.46957 20.9997 3.96086 20.789 3.58579 20.414C3.21071 20.0389 3 19.5302 3 18.9997V11.9997C2.99999 10.8178 3.23277 9.64751 3.68506 8.55557C4.13734 7.46364 4.80028 6.47148 5.636 5.63574"/>

    </svg>
  );
}
