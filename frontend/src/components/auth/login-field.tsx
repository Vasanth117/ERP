"use client";

import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export const loginInputClassName = cn(
  "box-border block h-11 w-full rounded-lg border border-[#d8dee8] bg-white",
  "px-3.5 text-[15px] leading-normal text-[#172b45]",
  "placeholder:text-[#94a3b8]",
  "transition-[border-color,box-shadow]",
  "focus:border-[#245dd8] focus:outline-none focus:ring-2 focus:ring-[#245dd8]/15",
  "disabled:cursor-not-allowed disabled:bg-[#f8fafc] disabled:opacity-70",
);

type LoginFieldProps = {
  id: string;
  label: string;
  hint?: string;
  error?: string;
} & InputHTMLAttributes<HTMLInputElement>;

export function LoginField({
  id,
  label,
  hint,
  error,
  className,
  ...props
}: LoginFieldProps) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-[15px] font-medium text-[#334155]">
        {label}
      </label>
      <input
        id={id}
        className={cn(loginInputClassName, error && "border-red-500 focus:ring-red-500/15", className)}
        aria-invalid={Boolean(error)}
        {...props}
      />
      {error ? (
        <p className="text-[15px] text-red-600">{error}</p>
      ) : hint ? (
        <p className="text-[15px] text-[#64748b]">{hint}</p>
      ) : null}
    </div>
  );
}