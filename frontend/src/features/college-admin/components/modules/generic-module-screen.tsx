"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { apiRequest } from "@/lib/api/client";
import { moduleApiMap } from "@/features/college-admin/config/module-api-map";
import {
  DataTable,
  DetailGrid,
  FormPlaceholder,
  SectionPanel,
  ToolbarRow,
  SearchField,
  columnsFromRows,
  rowsFromApi,
} from "@/features/college-admin/components/ui/college-admin-screen-ui";
import {
  QueryState,
  StatCard,
} from "@/features/college-admin/components/ui/query-state";

export type ModuleViewType =
  | "dashboard"
  | "list"
  | "detail"
  | "form"
  | "settings"
  | "report";

type Props = {
  moduleKey: string;
  slug: string;
  title: string;
  apiPath?: string;
  viewType?: ModuleViewType;
};

function resolveEndpoint(
  moduleKey: string,
  slug: string,
  apiPath?: string,
): { path: string; label: string } | null {
  if (apiPath) {
    return { path: apiPath, label: titleFromSlug(slug) };
  }
  const endpoints = moduleApiMap[moduleKey] ?? [];
  if (endpoints.length === 0) return null;
  const index = slug.endsWith("-dashboard") ? 0 : 0;
  const endpoint = endpoints[index] ?? endpoints[0];
  return endpoint ?? null;
}

function titleFromSlug(slug: string): string {
  return slug
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function recordCount(data: unknown): number {
  if (Array.isArray(data)) return data.length;
  if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>;
    if (Array.isArray(obj.items)) return obj.items.length;
    if (Array.isArray(obj.data)) return obj.data.length;
    if (obj.total != null && !Number.isNaN(Number(obj.total))) {
      return Number(obj.total);
    }
  }
  return data == null ? 0 : 1;
}

export function GenericModuleScreen({
  moduleKey,
  slug,
  title,
  apiPath,
  viewType = "list",
}: Props) {
  const endpoint = resolveEndpoint(moduleKey, slug, apiPath);
  const [search, setSearch] = useState("");

  const q = useQuery({
    queryKey: ["college-admin-module", moduleKey, slug, endpoint?.path],
    queryFn: async () => {
      if (!endpoint) return null;
      return await apiRequest<unknown>(endpoint.path);
    },
    enabled: Boolean(endpoint),
    retry: 1,
  });

  const rows = useMemo(() => {
    const base = rowsFromApi(q.data);
    if (!search.trim()) return base;
    const needle = search.toLowerCase();
    return base.filter((row) =>
      Object.values(row).some((v) => String(v).toLowerCase().includes(needle)),
    );
  }, [q.data, search]);

  const cols = columnsFromRows(rows);

  if (!endpoint) {
    return (
      <SectionPanel title={title} description="This frame is not bound to an API route yet.">
        <p className="text-sm text-[#607086]">
          Run <code className="text-[#245dd8]">py scripts/sync_college_admin_pages.py</code> after
          exporting Figma metadata for this module.
        </p>
      </SectionPanel>
    );
  }

  if (viewType === "form" || viewType === "settings") {
    return (
      <FormPlaceholder
        title={title}
        description={`Configuration screen for ${moduleKey}. Data loads from ${endpoint.path}.`}
      />
    );
  }

  const count = recordCount(q.data);

  return (
    <QueryState
      isLoading={q.isLoading}
      isError={q.isError}
      error={q.error}
      onRetry={() => void q.refetch()}
    >
      <div className="space-y-4">
        {viewType === "dashboard" ? (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Records" value={count} hint={title} />
            <StatCard label="Module" value={moduleKey} hint="College Admin" />
            <StatCard label="View" value="Overview" hint="CA screen" />
            <div className="flex items-center rounded-xl border border-[#dce3ec] bg-white p-4 shadow-[0px_1px_1px_rgba(23,43,69,0.04)]">
              <Button
                type="button"
                className="h-9 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]"
                onClick={() => void q.refetch()}
              >
                Refresh dashboard
              </Button>
            </div>
          </div>
        ) : null}

        <SectionPanel
          title={title}
          description={
            viewType === "report"
              ? "Summary and export view for institutional reporting."
              : viewType === "detail"
                ? "Record detail aligned with the Figma detail layout."
                : "List and filters aligned with the Figma table layout."
          }
          actions={
            viewType === "report" ? (
              <Button
                type="button"
                variant="outline"
                className="h-9 border-[#dce3ec] text-xs"
                disabled
              >
                Export
              </Button>
            ) : null
          }
        >
          <ToolbarRow onRefresh={() => void q.refetch()}>
            {(viewType === "list" || viewType === "dashboard" || viewType === "report") && (
              <SearchField value={search} onChange={setSearch} placeholder={`Search ${title}…`} />
            )}
          </ToolbarRow>

          {viewType === "detail" && rows.length <= 1 && rows[0] ? (
            <DetailGrid record={rows[0]} />
          ) : (
            <DataTable columns={cols.length ? cols : ["id", "name", "status"]} rows={rows} />
          )}
        </SectionPanel>
      </div>
    </QueryState>
  );
}