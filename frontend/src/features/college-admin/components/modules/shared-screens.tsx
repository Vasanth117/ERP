"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DataTable,
  SectionPanel,
} from "@/features/college-admin/components/ui/college-admin-screen-ui";
import { QueryState, StatCard } from "@/features/college-admin/components/ui/query-state";

/** Figma CA 24 — shared UI states and dialogs (pattern reference for all CA modules). */
export function SharedScreen({ slug, title }: { slug: string; title: string }) {
  switch (slug) {
    case "empty-state-no-records":
      return (
        <QueryState isLoading={false} isError={false} isEmpty emptyMessage="No records found for this filter.">
          <></>
        </QueryState>
      );
    case "empty-state-no-search-results":
      return (
        <SectionPanel title={title}>
          <QueryState
            isLoading={false}
            isError={false}
            isEmpty
            emptyMessage="No search results. Try adjusting keywords or filters."
          >
            <></>
          </QueryState>
        </SectionPanel>
      );
    case "loading-state":
      return <QueryState isLoading isError={false}><></></QueryState>;
    case "error-state-failed-to-load":
      return (
        <QueryState
          isLoading={false}
          isError
          error={new Error("Failed to load this section. The API may be unavailable.")}
          onRetry={() => window.location.reload()}
        >
          <></>
        </QueryState>
      );
    case "access-denied":
      return (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-8 text-center">
          <h2 className="text-lg font-semibold text-[#172b45]">Access denied</h2>
          <p className="mt-2 text-sm text-[#607086]">
            You do not have permission to view this institutional resource.
          </p>
        </div>
      );
    case "validation-errors-on-form":
      return <ValidationFormDemo title={title} />;
    case "confirm-delete-dialog":
      return <DialogDemo title={title} variant="delete" />;
    case "approve-reject-dialog":
      return <DialogDemo title={title} variant="approve" />;
    case "bulk-action-confirmation":
      return <DialogDemo title={title} variant="bulk" />;
    case "success-feedback":
      return (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-8 text-center">
          <p className="text-sm font-medium text-emerald-900">Changes saved successfully</p>
          <p className="mt-1 text-xs text-emerald-800">Success feedback pattern (Figma CA 24.10)</p>
        </div>
      );
    case "unsaved-changes-warning":
      return <DialogDemo title={title} variant="unsaved" />;
    default:
      return <PatternGallery title={title} />;
  }
}

function ValidationFormDemo({ title }: { title: string }) {
  return (
    <SectionPanel title={title}>
      <form className="max-w-md space-y-3" onSubmit={(e) => e.preventDefault()}>
        <label className="grid gap-1 text-xs text-[#607086]">
          Email
          <Input className="border-red-300" defaultValue="invalid" aria-invalid />
          <span className="text-red-600">Enter a valid institutional email address.</span>
        </label>
        <label className="grid gap-1 text-xs text-[#607086]">
          Department
          <Input className="border-[#dce3ec]" placeholder="Required" />
        </label>
        <Button type="submit" className="h-9 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]">
          Submit
        </Button>
      </form>
    </SectionPanel>
  );
}

function DialogDemo({
  title,
  variant,
}: {
  title: string;
  variant: "delete" | "approve" | "bulk" | "unsaved";
}) {
  const [open, setOpen] = useState(true);
  const copy = {
    delete: {
      body: "Delete this record? This action cannot be undone.",
      primary: "Delete",
      primaryClass: "bg-red-600 hover:bg-red-700",
    },
    approve: {
      body: "Approve or reject this institutional request?",
      primary: "Approve",
      primaryClass: "bg-[#245dd8] hover:bg-[#1f4fb8]",
    },
    bulk: {
      body: "Apply this action to 24 selected rows?",
      primary: "Confirm",
      primaryClass: "bg-[#245dd8] hover:bg-[#1f4fb8]",
    },
    unsaved: {
      body: "You have unsaved changes. Leave without saving?",
      primary: "Leave",
      primaryClass: "bg-amber-600 hover:bg-amber-700",
    },
  }[variant];

  if (!open) {
    return (
      <SectionPanel title={title}>
        <Button type="button" onClick={() => setOpen(true)} className="h-9 text-xs">
          Show dialog preview
        </Button>
      </SectionPanel>
    );
  }

  return (
    <SectionPanel title={title}>
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-[#172b45]/40 p-4"
        role="dialog"
        aria-modal
      >
        <div className="w-full max-w-md rounded-xl border border-[#dce3ec] bg-white p-6 shadow-lg">
          <h3 className="text-sm font-semibold text-[#172b45]">{title}</h3>
          <p className="mt-2 text-sm text-[#607086]">{copy.body}</p>
          <div className="mt-6 flex justify-end gap-2">
            <Button type="button" variant="outline" className="h-9 text-xs" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="button" className={`h-9 text-xs ${copy.primaryClass}`} onClick={() => setOpen(false)}>
              {copy.primary}
            </Button>
          </div>
        </div>
      </div>
    </SectionPanel>
  );
}

function PatternGallery({ title }: { title: string }) {
  return (
    <SectionPanel title={title}>
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="List pattern" value={3} hint="Table + toolbar" />
        <StatCard label="Form pattern" value={5} hint="Labels + validation" />
        <StatCard label="Dialog pattern" value={4} hint="Modal actions" />
      </div>
      <div className="mt-6">
        <DataTable
          columns={["name", "status", "updated"]}
          rows={[
            { name: "Sample row", status: "Active", updated: "Today" },
            { name: "Pattern reference", status: "Draft", updated: "—" },
          ]}
        />
      </div>
    </SectionPanel>
  );
}