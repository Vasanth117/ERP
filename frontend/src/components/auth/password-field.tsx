"use client";

import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import type { UseFormRegisterReturn } from "react-hook-form";

import { loginInputClassName } from "@/components/auth/login-field";
import { cn } from "@/lib/utils";

type PasswordFieldProps = {
  id: string;
  label: string;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
  showForgotLink?: boolean;
  register: UseFormRegisterReturn;
};

export function PasswordField({
  id,
  label,
  placeholder = "Enter your password",
  disabled,
  error,
  showForgotLink = false,
  register,
}: PasswordFieldProps) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <label
          htmlFor={id}
          className="text-[13px] font-semibold tracking-tight text-[#334155]"
        >
          {label}
        </label>
        {showForgotLink ? (
          <span
            className="text-[13px] font-medium text-[#245dd8] opacity-60"
            aria-hidden
          >
            Forgot password?
          </span>
        ) : null}
      </div>
      <div className="relative">
        <input
          id={id}
          type={visible ? "text" : "password"}
          placeholder={placeholder}
          autoComplete="current-password"
          disabled={disabled}
          className={cn(
            loginInputClassName,
            "pr-12",
            error && "border-red-500 focus:ring-red-500/15",
          )}
          aria-invalid={Boolean(error)}
          {...register}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-[#64748b] transition-colors hover:bg-[#eef2f7] hover:text-[#0f2744]"
          aria-label={visible ? "Hide password" : "Show password"}
          tabIndex={-1}
        >
          {visible ? (
            <EyeOff className="size-5" aria-hidden />
          ) : (
            <Eye className="size-5" aria-hidden />
          )}
        </button>
      </div>
      {error ? (
        <p className="text-[12px] font-medium text-red-600">{error}</p>
      ) : null}
    </div>
  );
}