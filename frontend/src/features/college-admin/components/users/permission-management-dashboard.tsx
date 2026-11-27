"use client";

import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import { toast } from "sonner";

import { CheckIcon } from "@/components/icons/erp/generated/check";
import { TriangleAlertIcon } from "@/components/icons/erp/generated/triangle-alert";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useDownloadPermissionMatrix,
  usePermissionManagementPage,
  useSavePermissionManagementMatrix,
} from "@/features/college-admin/hooks/use-permission-management";
import type {
  PermissionManagementMatrixChange,
  PermissionMatrixGroup,
} from "@/features/college-admin/types/permission-management";
import { cn } from "@/lib/utils";

type CellState = Record<string, boolean>;

function cellId(columnKey: string, permissionCode: string) {
  return `${columnKey}::${permissionCode}`;
}

function buildStateFromGroups(groups: PermissionMatrixGroup[]): CellState {
  const state: CellState = {};
  for (const group of groups) {
    for (const row of group.rows) {
      for (const cell of row.cells) {
        state[cellId(cell.column_key, row.permission_code)] = cell.checked;
      }
    }
  }
  return state;
}

function cloneGroups(groups: PermissionMatrixGroup[]): PermissionMatrixGroup[] {
  return groups.map((group) => ({
    ...group,
    rows: group.rows.map((row) => ({
      ...row,
      cells: row.cells.map((cell) => ({ ...cell })),
    })),
  }));
}

function applyStateToGroups(groups: PermissionMatrixGroup[], state: CellState): PermissionMatrixGroup[] {
  return groups.map((group) => ({
    ...group,
    rows: group.rows.map((row) => ({
      ...row,
      cells: row.cells.map((cell) => ({
        ...cell,
        checked: state[cellId(cell.column_key, row.permission_code)] ?? cell.checked,
      })),
    })),
  }));
}

export function PermissionManagementDashboard() {
  const pageQuery = usePermissionManagementPage();
  const saveMutation = useSavePermissionManagementMatrix();
  const downloadMutation = useDownloadPermissionMatrix();

  const [baseline, setBaseline] = useState<CellState>({});
  const [matrixState, setMatrixState] = useState<CellState>({});
  const [displayGroups, setDisplayGroups] = useState<PermissionMatrixGroup[]>([]);

  useEffect(() => {
    if (!pageQuery.data) return;
    const initial = buildStateFromGroups(pageQuery.data.groups);
    setBaseline(initial);
    setMatrixState(initial);
    setDisplayGroups(cloneGroups(pageQuery.data.groups));
  }, [pageQuery.data]);

  const data = pageQuery.data;

  const columnByKey = useMemo(() => {
    const map = new Map<string, { label: string; institution_role_id: string | null; editable: boolean }>();
    for (const col of data?.columns ?? []) {
      map.set(col.column_key, {
        label: col.label,
        institution_role_id: col.institution_role_id,
        editable: col.editable,
      });
    }
    return map;
  }, [data?.columns]);

  const dirtyChanges = useMemo(() => {
    if (!data) return [] as PermissionManagementMatrixChange[];
    const changes: PermissionManagementMatrixChange[] = [];

    for (const group of data.groups) {
      for (const row of group.rows) {
        for (const cell of row.cells) {
          const id = cellId(cell.column_key, row.permission_code);
          const original = baseline[id];
          const current = matrixState[id];
          if (original === undefined || current === original) continue;

          const col = columnByKey.get(cell.column_key);
          if (!col?.institution_role_id || !col.editable) continue;

          changes.push({
            institution_role_id: col.institution_role_id,
            permission_code: row.permission_code,
            granted: current,
          });
        }
      }
    }
    return changes;
  }, [baseline, matrixState, data, columnByKey]);

  const changeSummaries = useMemo(() => {
    if (!data) return [];
    const lines: string[] = [];
    for (const group of data.groups) {
      for (const row of group.rows) {
        for (const cell of row.cells) {
          const id = cellId(cell.column_key, row.permission_code);
          if (baseline[id] === matrixState[id]) continue;
          const col = columnByKey.get(cell.column_key);
          if (!col) continue;
          const action = matrixState[id] ? data.change_on_label : data.change_off_label;
          lines.push(`${col.label} · ${row.label} → ${action}`);
        }
      }
    }
    return lines;
  }, [baseline, matrixState, data, columnByKey]);

  const toggleCell = useCallback(
    (columnKey: string, permissionCode: string, editable: boolean, checked: boolean) => {
      if (!editable) return;
      setMatrixState((prev) => {
        const next = { ...prev, [cellId(columnKey, permissionCode)]: checked };
        if (data) {
          setDisplayGroups(applyStateToGroups(data.groups, next));
        }
        return next;
      });
    },
    [data],
  );

  const handleSave = useCallback(() => {
    if (!data?.can_save) {
      toast.error("You cannot modify permissions");
      return;
    }
    if (!dirtyChanges.length) {
      toast.message("No changes to save");
      return;
    }
    saveMutation.mutate(dirtyChanges, {
      onSuccess: (saved) => {
        const next = buildStateFromGroups(saved.groups);
        setBaseline(next);
        setMatrixState(next);
        setDisplayGroups(cloneGroups(saved.groups));
        toast.success("Permission matrix saved");
      },
      onError: onCollegeAdminMutationError,
    });
  }, [data?.can_save, dirtyChanges, saveMutation]);

  const handleExport = useCallback(() => {
    downloadMutation.mutate(undefined, {
      onError: onCollegeAdminMutationError,
    });
  }, [downloadMutation]);

  const unsavedCount = changeSummaries.length;
  const isBusy = saveMutation.isPending || downloadMutation.isPending;

  return (
    <div className="space-y-5" data-figma-frame="69:126902">
      <CollegeAdminModulePageHeading title={data?.page_title ?? "Permission Management"} subtitle={data?.page_subtitle} actions={<><button
            type="button"
            disabled={!data || isBusy}
            onClick={() => handleExport()}
            className="inline-flex h-9 items-center gap-1.5 rounded-md border border-[#dce3ec] bg-white px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb] disabled:opacity-50"
          >
            <CollegeAdminDownload className="size-3.5" aria-hidden />
            {data?.export_matrix_label ?? "Export matrix"}
          </button>
          <button
            type="button"
            disabled={!data?.can_save || isBusy}
            onClick={() => handleSave()}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-[#245dd8] px-4 text-xs font-medium text-white hover:bg-[#1d4ed8] disabled:opacity-50"
          >
            <CheckIcon className="size-3.5" aria-hidden />
            {data?.save_changes_label ?? "Save changes"}
          </button></>} />

      {data?.matrix_read_only_reason ? (
        <div className="rounded-xl border border-[#e8ecf2] bg-[#f9fafb] px-4 py-3 text-[13px] text-[#6b7280]">
          {data.matrix_read_only_reason}
        </div>
      ) : null}

      {data && unsavedCount > 0 ? (
        <div className="rounded-xl border border-[#fde68a] bg-[#fffbeb] px-4 py-3.5">
          <div className="flex flex-wrap items-start gap-2">
            <TriangleAlertIcon className="mt-0.5 size-4 shrink-0 text-[#d97706]" aria-hidden />
            <div className="min-w-0 flex-1">
              <p className="text-[13px] font-semibold text-[#92400e]">
                {unsavedCount} {data.unsaved_changes_title}
              </p>
              <ul className="mt-1.5 space-y-0.5 text-[12px] text-[#a16207]">
                {changeSummaries.slice(0, 4).map((line) => (
                  <li key={line}>{line}</li>
                ))}
                {changeSummaries.length > 4 ? (
                  <li>+ {changeSummaries.length - 4} more</li>
                ) : null}
              </ul>
              <p className="mt-2 text-[11px] text-[#b45309]">{data.unsaved_changes_note}</p>
            </div>
          </div>
        </div>
      ) : null}

      <QueryState query={pageQuery}>
        {data ? (
          <section className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <div className="flex flex-col gap-1 border-b border-[#f1f5f9] px-5 py-3.5 sm:flex-row sm:items-center sm:justify-between">
              <h3 className="text-[14px] font-semibold text-[#111827]">{data.matrix_section_title}</h3>
              <p className="text-[12px] text-[#6b7280]">{data.matrix_legend}</p>
            </div>
            <div className="overflow-x-auto px-2 pb-2">
              <table className="w-full min-w-[56rem] border-collapse text-[12px]">
                <thead>
                  <tr className="border-b border-[#e8ecf2] text-left text-[11px] font-semibold uppercase tracking-wide text-[#6b7280]">
                    {data.permission_columns.map((col, idx) => (
                      <th
                        key={`${col}-${idx}`}
                        className={cn(
                          "px-3 py-3",
                          idx === 0 ? "w-[26%] text-left" : "w-[9%] text-center",
                        )}
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {displayGroups.map((group) => (
                    <Fragment key={group.group_key}>
                      <tr>
                        <td
                          colSpan={data.permission_columns.length}
                          className="bg-[#f9fafb] px-3 py-2 text-[12px] font-semibold text-[#374151]"
                        >
                          {group.group_label}
                        </td>
                      </tr>
                      {group.rows.map((row) => (
                        <tr key={row.row_key} className="border-b border-[#f1f5f9]">
                          <td className="px-3 py-2.5 text-[13px] text-[#374151]">{row.label}</td>
                          {row.cells.map((cell) => (
                            <td key={cell.column_key} className="px-3 py-2.5 text-center">
                              <input
                                type="checkbox"
                                className={cn(
                                  "size-4 rounded border-[#cbd5e1] text-[#245dd8] focus:ring-[#245dd8]/30",
                                  !cell.editable && "cursor-not-allowed opacity-70",
                                )}
                                checked={matrixState[cellId(cell.column_key, row.permission_code)] ?? cell.checked}
                                disabled={!cell.editable || isBusy}
                                onChange={(e) =>
                                  toggleCell(
                                    cell.column_key,
                                    row.permission_code,
                                    cell.editable,
                                    e.target.checked,
                                  )
                                }
                              />
                            </td>
                          ))}
                        </tr>
                      ))}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}
      </QueryState>
    </div>
  );
}