import type { SVGProps } from "react";

import { cn } from "@/lib/utils";

export function PaperclipIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
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
      <path d="M21.44 11.0499L12.25 20.2399C11.1242 21.3658 9.59718 21.9982 8.005 21.9982C6.41282 21.9982 4.88584 21.3658 3.76 20.2399C2.63416 19.1141 2.00166 17.5871 2.00166 15.9949C2.00166 14.4027 2.63416 12.8758 3.76 11.7499L12.33 3.17991C13.0806 2.42802 14.0991 2.00509 15.1615 2.00415C16.2239 2.00321 17.2431 2.42435 17.995 3.17491C18.7469 3.92547 19.1698 4.94398 19.1708 6.00638C19.1717 7.06877 18.7506 8.08802 18 8.83991L9.41 17.4099C9.03472 17.7852 8.52573 17.996 7.995 17.996C7.46427 17.996 6.95528 17.7852 6.58 17.4099C6.20472 17.0346 5.99389 16.5256 5.99389 15.9949C5.99389 15.4642 6.20472 14.9552 6.58 14.5799L15.07 6.09991"/>

    </svg>
  );
}
