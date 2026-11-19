"use client";

import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";

type QueryStateProps = {
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
  isEmpty?: boolean;
  emptyMessage?: string;
  onRetry?: () => void;
  children: ReactNode;
};

export function QueryState({
  isLoading,
  isError,
  error,
  isEmpty,
  emptyMessage = "No records found.",
  onRetry,
  children,
}: QueryStateProps) {
  if (isLoading) {
    return (
      <StatusPanel
        className="rounded-xl border border-[#dce3ec] bg-white p-8 text-center text-sm text-[#607086]"
        message="Loading…"
      />
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-900">
        <p className="font-medium">Could not load this section</p>
        <p className="mt-1 text-red-800/90">{error?.message ?? "Unknown error"}</p>
        {onRetry ? (
          <Button type="button" variant="outline" className="mt-4" onClick={onRetry}>
            Retry
          </Button>
        ) : null}
      </div>
    );
  }

  if (isEmpty) {
    return (
      <StatusPanel
        className="rounded-xl border border-dashed border-[#dce3ec] bg-white p-8 text-center text-sm text-[#607086]"
        message={emptyMessage}
      />
    );
  }

  return children;
}

function StatusPanel({
  className,
  message,
}: {
  className: string;
  message: string;
}) {
  return <div className={className}>{message}</div>;
}

export function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div className="rounded-xl border border-[#dce3ec] bg-white p-4 shadow-[0px_1px_1px_rgba(23,43,69,0.04)]">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-[#8a98aa]">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold text-[#172b45]">{value}</p>
      {hint ? <p className="mt-1 text-xs text-[#607086]">{hint}</p> : null}
    </div>
  );
}