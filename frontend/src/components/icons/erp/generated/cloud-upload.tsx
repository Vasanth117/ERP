import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function CloudUploadIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M12 13V21"/>
      <path d="M4 14.8988C3.25704 14.1397 2.69657 13.2215 2.36104 12.2137C2.0255 11.2059 1.92371 10.135 2.06336 9.08208C2.20302 8.02913 2.58046 7.02178 3.1671 6.13631C3.75374 5.25085 4.53419 4.51049 5.44934 3.97133C6.36448 3.43216 7.39033 3.10833 8.44917 3.02435C9.50801 2.94038 10.5721 3.09846 11.5608 3.48664C12.5495 3.87481 13.4369 4.48289 14.1557 5.26481C14.8746 6.04674 15.4061 6.98201 15.71 7.99978H17.5C18.4655 7.99967 19.4055 8.3101 20.181 8.88522C20.9565 9.46033 21.5265 10.2696 21.8068 11.1936C22.087 12.1175 22.0627 13.1071 21.7373 14.0162C21.412 14.9252 20.8029 15.7055 20 16.2418"/>
      <path d="M8 17L12 13L16 17"/>

    </svg>
  );
}
