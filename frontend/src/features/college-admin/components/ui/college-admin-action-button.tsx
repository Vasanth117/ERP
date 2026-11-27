"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";

type BaseProps = {
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
  type?: "button" | "submit";
  onClick?: () => void;
};

const primaryClass =
  "inline-flex h-9 items-center justify-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-semibold text-white shadow-[0_1px_2px_rgba(36,93,216,0.35)] transition-colors hover:bg-[#1f4fb8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#245dd8] disabled:cursor-not-allowed disabled:bg-[#9bb5eb] disabled:text-white disabled:shadow-none";

const secondaryClass =
  "inline-flex h-9 items-center justify-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-semibold text-[#374151] shadow-[0_1px_2px_rgba(15,23,42,0.04)] transition-colors hover:bg-[#f9fafb] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#dce3ec] disabled:cursor-not-allowed disabled:text-[#9ca3af] disabled:shadow-none";

export function CollegeAdminPrimaryButton({ className, ...props }: BaseProps) {
  return (
    <button
      type={props.type ?? "button"}
      disabled={props.disabled}
      onClick={props.onClick}
      className={cn(primaryClass, className)}
    >
      {props.children}
    </button>
  );
}

export function CollegeAdminSecondaryButton({ className, ...props }: BaseProps) {
  return (
    <button
      type={props.type ?? "button"}
      disabled={props.disabled}
      onClick={props.onClick}
      className={cn(secondaryClass, className)}
    >
      {props.children}
    </button>
  );
}

export function CollegeAdminPrimaryLink({
  href,
  children,
  className,
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Link href={href} className={cn(primaryClass, "no-underline", className)}>
      {children}
    </Link>
  );
}

export function CollegeAdminSecondaryLink({
  href,
  children,
  className,
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Link href={href} className={cn(secondaryClass, "no-underline", className)}>
      {children}
    </Link>
  );
}

export { primaryClass as collegeAdminPrimaryActionClass, secondaryClass as collegeAdminSecondaryActionClass };