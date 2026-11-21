"use client";

import type { UseQueryResult } from "@tanstack/react-query";
import Link from "next/link";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";

type QueryStateProps = {
  isLoading?: boolean;
  isError?: boolean;
  error?: Error | null;
  isEmpty?: boolean;
  emptyMessage?: string;
  onRetry?: () => void;
  query?: Pick<UseQueryResult, "isLoading" | "isError" | "error" | "refetch">;
  children: ReactNode;
};

export function QueryState({
  isLoading: isLoadingProp,
  isError: isErrorProp,
  error: errorProp,
  isEmpty,
  emptyMessage = "No records found.",
  onRetry: onRetryProp,
  query,
  children,
}: QueryStateProps) {
  const isLoading = isLoadingProp ?? query?.isLoading ?? false;
  const isError = isErrorProp ?? query?.isError ?? false;
  const error = errorProp ?? (query?.error as Error | null | undefined);
  const onRetry = onRetryProp ?? (query ? () => void query.refetch() : undefined);
  if (isLoading) {
    return (
      <StatusPanel
        className="rounded-xl border border-[#dce3ec] bg-white p-8 text-center text-sm text-[#607086]"
        message="Loading…"
      />
    );
  }

  if (isError) {
    const status = (error as Error & { status?: number })?.status;
    const unauthorized = status === 401;
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-900">
        <p className="font-medium">
          {unauthorized ? "Sign in required" : "Could not load this section"}
        </p>
        <p className="mt-1 text-red-800/90">
          {unauthorized
            ? "Your session is missing or expired. Sign in with the demo college account to load live data."
            : (error?.message ?? "Unknown error")}
        </p>
        {unauthorized ? (
          <Link
            href="/login"
            className="mt-4 inline-flex h-9 items-center rounded-lg bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1f4fb8]"
          >
            Go to login
          </Link>
        ) : onRetry ? (
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

export { StatCard, CollegeAdminKpiCard, CollegeAdminKpiGrid } from "@/features/college-admin/components/ui/college-admin-kpi-card";