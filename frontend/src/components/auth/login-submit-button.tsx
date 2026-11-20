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
        "mt-2 w-full rounded-lg border border-[#1e52c4] bg-[#245dd8] px-4 py-3",
        "text-[15px] font-semibold text-white",
        "transition-colors hover:bg-[#1e52c4]",
        "focus:outline-none focus:ring-4 focus:ring-[#245dd8]/25",
        "disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
    >
      {children}
    </button>
  );
}