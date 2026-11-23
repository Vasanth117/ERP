"use client";

import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export const loginInputClassName = cn(
  "box-border block h-12 w-full rounded-xl border border-[#dce3ec] bg-[#fafbfd]",
  "px-4 text-[14px] font-normal leading-normal text-[#0f2744]",
  "placeholder:text-[#94a3b8]",
  "shadow-[0_1px_2px_rgba(15,39,69,0.04)]",
  "transition-[border-color,box-shadow,background-color]",
  "hover:border-[#c5d0de] hover:bg-white",
  "focus:border-[#245dd8] focus:bg-white focus:outline-none focus:ring-[3px] focus:ring-[#245dd8]/12",
  "disabled:cursor-not-allowed disabled:bg-[#f4f6f9] disabled:opacity-70",
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
    <div className="space-y-2">
      <label
        htmlFor={id}
        className="block text-[13px] font-semibold tracking-tight text-[#334155]"
      >
        {label}
      </label>
      <input
        id={id}
        className={cn(loginInputClassName, error && "border-red-500 focus:ring-red-500/15", className)}
        aria-invalid={Boolean(error)}
        {...props}
      />
      {error ? (
        <p className="text-[12px] font-medium text-red-600">{error}</p>
      ) : hint ? (
        <p className="text-[12px] text-[#64748b]">{hint}</p>
      ) : null}
    </div>
  );
}