"use client";

import { cn } from "@/lib/utils";

type LoginSubmitButtonProps = {
  disabled?: boolean;
  children: React.ReactNode;
  className?: string;
};

export function LoginSubmitButton({
  disabled,
  children,
  className,
}: LoginSubmitButtonProps) {
  return (
    <button
      type="submit"
      disabled={disabled}
      className={cn(
        "mt-1 h-12 w-full rounded-xl border border-[#1e52c4] bg-[#245dd8] px-4",
        "text-[14px] font-semibold tracking-tight text-white",
        "shadow-[0_4px_14px_rgba(36,93,216,0.28)]",
        "transition-[background-color,box-shadow,transform]",
        "hover:bg-[#1e52c4] hover:shadow-[0_6px_18px_rgba(36,93,216,0.32)]",
        "active:scale-[0.99]",
        "focus:outline-none focus:ring-[3px] focus:ring-[#245dd8]/30",
        "disabled:cursor-not-allowed disabled:opacity-60 disabled:shadow-none",
        className,
      )}
    >
      {children}
    </button>
  );
}