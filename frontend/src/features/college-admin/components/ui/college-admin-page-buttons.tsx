import Link from "next/link";
import type { ButtonHTMLAttributes, ComponentProps } from "react";

import { cn } from "@/lib/utils";

export const collegeAdminOutlineButtonClass =
  "inline-flex h-9 items-center justify-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50";

export const collegeAdminPrimaryButtonClass =
  "inline-flex h-9 items-center justify-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8] disabled:opacity-50";

/** Backend labels sometimes include a leading "+"; icons already convey "add". */
export function collegeAdminActionLabel(label: string): string {
  return label.replace(/^\+\s*/, "").trim();
}

export function CollegeAdminOutlineButton({
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button type="button" className={cn(collegeAdminOutlineButtonClass, className)} {...props} />;
}

export function CollegeAdminPrimaryButton({
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button type="button" className={cn(collegeAdminPrimaryButtonClass, className)} {...props} />;
}

export function CollegeAdminOutlineLink({
  className,
  ...props
}: ComponentProps<typeof Link>) {
  return <Link className={cn(collegeAdminOutlineButtonClass, className)} {...props} />;
}

export function CollegeAdminPrimaryLink({
  className,
  ...props
}: ComponentProps<typeof Link>) {
  return <Link className={cn(collegeAdminPrimaryButtonClass, className)} {...props} />;
}