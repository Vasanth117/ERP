"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { CollegeAdminModulePageHeading } from "@/features/college-admin/components/layout/college-admin-module-page-heading";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Building2Icon } from "@/components/icons/erp/generated/building-2";
import { ChevronRightIcon } from "@/components/icons/erp/generated/chevron-right";
import { LayersIcon } from "@/components/icons/erp/generated/layers";
import { PencilIcon } from "@/components/icons/erp/generated/pencil";
import { UsersIcon } from "@/components/icons/erp/generated/users";
import { CollegeAdminDownload } from "@/features/college-admin/components/layout/college-admin-erp-icons";
import {
  CollegeAdminOutlineButton,
  CollegeAdminOutlineLink,
  CollegeAdminPrimaryLink,
} from "@/features/college-admin/components/ui/college-admin-page-buttons";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import { useOrganizationalHierarchyPage } from "@/features/college-admin/hooks/use-organizational-hierarchy";
import type {
  OrganizationalHierarchyEditAction,
  OrganizationalHierarchyNode,
} from "@/features/college-admin/types/organizational-hierarchy";
import { cn } from "@/lib/utils";

function HierarchyIcon({ slug }: { slug: string }) {
  if (slug === "building") return <Building2Icon className="size-4 shrink-0 text-[#245dd8]" aria-hidden />;
  if (slug === "layers") return <LayersIcon className="size-4 shrink-0 text-[#6b7280]" aria-hidden />;
  return <UsersIcon className="size-4 shrink-0 text-[#6b7280]" aria-hidden />;
}

function StatusPill({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    info: "bg-[#3b82f6]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium", styles[key])}>
      <span className={cn("size-1.5 rounded-full", dot[key])} />
      {label}
    </span>
  );
}

function InfoBadge({ label, tone }: { label: string; tone: string }) {
  const styles: Record<string, string> = {
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-medium", styles[key])}>{label}</span>
  );
}


function collectDefaultExpanded(nodes: OrganizationalHierarchyNode[], acc: Set<string>) {
  for (const node of nodes) {
    if (node.default_expanded && node.children.length) {
      acc.add(node.node_id);
    }
    collectDefaultExpanded(node.children, acc);
  }
}

function hierarchyUrlParams(searchParams: URLSearchParams, patch: { selectedNodeId?: string; edit?: boolean }) {
  const params = new URLSearchParams(searchParams.toString());
  if (patch.selectedNodeId !== undefined) {
    if (patch.selectedNodeId) params.set("selected_node_id", patch.selectedNodeId);
    else params.delete("selected_node_id");
  }
  if (patch.edit !== undefined) {
    if (patch.edit) params.set("edit", "1");
    else params.delete("edit");
  }
  return params.toString();
}

function HierarchyEditActionLink({ action }: { action: OrganizationalHierarchyEditAction }) {
  if (action.action_type === "primary") {
    return (
      <CollegeAdminPrimaryLink href={action.href} className="w-full">
        {action.label}
      </CollegeAdminPrimaryLink>
    );
  }
  return (
    <CollegeAdminOutlineLink href={action.href} className="w-full">
      {action.label}
    </CollegeAdminOutlineLink>
  );
}

export function OrganizationalHierarchyDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const editMode = searchParams.get("edit") === "1" || searchParams.get("edit") === "true";
  const selectedNodeId = searchParams.get("selected_node_id") ?? undefined;

  const { data, isLoading, isError, error, refetch, isFetching } = useOrganizationalHierarchyPage(
    selectedNodeId,
    editMode,
  );

  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const selectNode = useCallback(
    (nodeId: string) => {
      const qs = hierarchyUrlParams(searchParams, { selectedNodeId: nodeId, edit: editMode ? true : undefined });
      router.replace(qs ? `?${qs}` : "", { scroll: false });
    },
    [editMode, router, searchParams],
  );

  useEffect(() => {
    if (!data?.tree) return;
    const defaults = new Set<string>();
    collectDefaultExpanded(data.tree, defaults);
    setExpanded((prev) => {
      const merged = new Set(prev);
      defaults.forEach((id) => merged.add(id));
      return merged;
    });
    if (!selectedNodeId && data.selected_unit?.node_id) {
      selectNode(data.selected_unit.node_id);
    }
  }, [data, selectedNodeId, selectNode]);

  const handleExport = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `organizational-hierarchy-${new Date(data.generated_at).toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const toggleExpanded = (nodeId: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  };

  const treeContent = useMemo(() => {
    if (!data?.tree) return null;
    return (
      <HierarchyTree
        nodes={data.tree}
        expanded={expanded}
        selectedNodeId={data.selected_unit?.node_id}
        onToggle={toggleExpanded}
        onSelect={selectNode}
      />
    );
  }, [data, expanded, selectNode]);

  return (
    <div className="space-y-5" data-figma-frame="69:134048">
      <CollegeAdminModulePageHeading title={data?.page_title ?? "Organizational Hierarchy"} subtitle={data?.page_subtitle ?? "Reporting structure from governing council to departments"} actions={<><CollegeAdminOutlineButton onClick={handleExport} disabled={isLoading || !data}>
            <CollegeAdminDownload className="size-3.5" aria-hidden />
            {data?.export_label ?? "Export chart"}
          </CollegeAdminOutlineButton>
          <CollegeAdminPrimaryLink
            href={
              data?.edit_structure_href ??
              "/college-admin/organization/organizational-hierarchy?edit=1"
            }
          >
            <PencilIcon className="size-3.5" aria-hidden />
            {data?.edit_structure_label ?? "Edit structure"}
          </CollegeAdminPrimaryLink></>} />

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()} isEmpty={false}>
        {data ? (
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_18.5rem]">
            <section className="rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
              <div className="border-b border-[#f1f5f9] px-5 py-3.5">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.structure_section_title}</h3>
                <p className="mt-0.5 text-[12px] text-[#6b7280]">{data.structure_section_hint}</p>
              </div>
              <div className={cn("min-h-[20rem] px-3 py-4", isFetching && "opacity-60")}>{treeContent}</div>
            </section>

            <aside className="space-y-4">
              {data.edit_mode && data.edit_panel_title ? (
                <section className="rounded-xl border border-[#dbeafe] bg-[#f8fafc] p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="text-[14px] font-semibold text-[#111827]">{data.edit_panel_title}</h3>
                  {data.edit_panel_hint ? (
                    <p className="mt-1.5 text-[12px] leading-relaxed text-[#6b7280]">{data.edit_panel_hint}</p>
                  ) : null}
                  {data.setup_edit_actions.length > 0 ? (
                    <div className="mt-4 flex flex-col gap-2">
                      {data.setup_edit_actions.map((action) => (
                        <HierarchyEditActionLink key={action.action_key} action={action} />
                      ))}
                    </div>
                  ) : null}
                </section>
              ) : null}

              {data.selected_unit ? (
                <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                  <h3 className="text-[14px] font-semibold text-[#111827]">Selected unit</h3>
                  <dl className="mt-4 space-y-3 text-[13px]">
                    <DetailRow label="Unit" value={data.selected_unit.unit_label} />
                    <DetailRow label="Reports to" value={data.selected_unit.reports_to_label} />
                    <DetailRow label="Head" value={data.selected_unit.head_label} />
                    <DetailRow label="Members" value={data.selected_unit.members_label} />
                  </dl>
                  {data.edit_mode && data.selected_unit.edit_actions.length > 0 ? (
                    <div className="mt-4 border-t border-[#f1f5f9] pt-4">
                      <p className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">Unit actions</p>
                      <div className="mt-2 flex flex-col gap-2">
                        {data.selected_unit.edit_actions.map((action) => (
                          <HierarchyEditActionLink key={action.action_key} action={action} />
                        ))}
                      </div>
                    </div>
                  ) : null}
                </section>
              ) : null}

              <section className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
                <h3 className="text-[14px] font-semibold text-[#111827]">{data.summary_section_title}</h3>
                <ul className="mt-4 divide-y divide-[#f1f5f9]">
                  {data.summary_items.map((item) => (
                    <li key={item.key} className="flex items-center justify-between py-2.5 text-[13px]">
                      <span className="text-[#6b7280]">{item.label}</span>
                      <span className="font-semibold tabular-nums text-[#111827]">{item.value}</span>
                    </li>
                  ))}
                </ul>
              </section>
            </aside>
          </div>
        ) : null}
      </QueryState>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[11px] font-medium uppercase tracking-wide text-[#9ca3af]">{label}</dt>
      <dd className="mt-0.5 font-medium text-[#111827]">{value}</dd>
    </div>
  );
}

function HierarchyTree({
  nodes,
  expanded,
  selectedNodeId,
  onToggle,
  onSelect,
}: {
  nodes: OrganizationalHierarchyNode[];
  expanded: Set<string>;
  selectedNodeId?: string;
  onToggle: (nodeId: string) => void;
  onSelect: (nodeId: string) => void;
}) {
  return (
    <ul className="space-y-0">
      {nodes.map((node) => (
        <HierarchyNodeRow
          key={node.node_id}
          node={node}
          expanded={expanded}
          selectedNodeId={selectedNodeId}
          onToggle={onToggle}
          onSelect={onSelect}
        />
      ))}
    </ul>
  );
}

function HierarchyNodeRow({
  node,
  expanded,
  selectedNodeId,
  onToggle,
  onSelect,
}: {
  node: OrganizationalHierarchyNode;
  expanded: Set<string>;
  selectedNodeId?: string;
  onToggle: (nodeId: string) => void;
  onSelect: (nodeId: string) => void;
}) {
  const hasChildren = node.children.length > 0;
  const isOpen = expanded.has(node.node_id);
  const isSelected = selectedNodeId === node.node_id;
  const paddingLeft = 12 + node.depth * 20;

  return (
    <li>
      <div
        className={cn(
          "group flex items-start gap-2 rounded-lg py-2 pr-2 transition-colors",
          isSelected ? "bg-[#eff6ff]" : "hover:bg-[#f9fafb]",
        )}
        style={{ paddingLeft }}
      >
        {hasChildren ? (
          <button
            type="button"
            aria-label={isOpen ? "Collapse" : "Expand"}
            className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded hover:bg-[#e5e7eb]"
            onClick={(e) => {
              e.stopPropagation();
              onToggle(node.node_id);
            }}
          >
            <ChevronRightIcon
              className={cn("size-3.5 text-[#6b7280] transition-transform", isOpen && "rotate-90")}
              aria-hidden
            />
          </button>
        ) : (
          <span className="size-6 shrink-0" />
        )}
        <button
          type="button"
          className="flex min-w-0 flex-1 items-start gap-2 text-left"
          onClick={() => {
            onSelect(node.node_id);
            if (hasChildren) onToggle(node.node_id);
          }}
        >
          <HierarchyIcon slug={node.icon_slug} />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[13px] font-semibold text-[#111827]">{node.title}</span>
              {node.badge_label ? <InfoBadge label={node.badge_label} tone={node.badge_tone ?? "info"} /> : null}
              {node.status_label ? <StatusPill label={node.status_label} tone={node.status_tone ?? "muted"} /> : null}
            </div>
            {node.subtitle ? (
              <p className="mt-0.5 text-[12px] leading-snug text-[#6b7280]">{node.subtitle}</p>
            ) : null}
          </div>
        </button>
      </div>
      {hasChildren && isOpen ? (
        <ul>
          {node.children.map((child) => (
            <HierarchyNodeRow
              key={child.node_id}
              node={child}
              expanded={expanded}
              selectedNodeId={selectedNodeId}
              onToggle={onToggle}
              onSelect={onSelect}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}