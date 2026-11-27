"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Input } from "@/components/ui/input";
import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import {
  ProfileFormField,
  ProfilePageHeading,
  ProfilePanel,
} from "@/features/student/components/ui/student-profile-ui";
import {
  STUDENT_BTN_OUTLINE,
  STUDENT_BTN_PRIMARY,
} from "@/features/student/components/ui/student-portal-tokens";
import {
  ProfileUpdateRequestTabs,
  type ProfileUpdateRequestTab,
} from "@/features/student/components/ui/profile-update-request-tabs";
import { QueryState, formatDateTime } from "@/features/student/components/ui/student-screen-ui";
import type { ProfileCorrectionRead } from "@/features/student/api/portal-documents";
import {
  useProfileCorrections,
  useSubmitProfileCorrection,
} from "@/features/student/hooks/use-student-profile-corrections";
import { useAcademicDetails } from "@/features/student/hooks/use-student-academics";
import { useStudentProfile } from "@/features/student/hooks/use-student-profile";
import { profileCorrectionCurrentValue } from "@/features/student/lib/profile-correction-current-value";
import {
  PROFILE_CORRECTION_FIELD_OPTIONS,
  type ProfileCorrectionFieldName,
  isProfileCorrectionFieldName,
  profileCorrectionFieldApprover,
  profileCorrectionFieldLabel,
} from "@/features/student/lib/profile-correction-fields";
import { cn } from "@/lib/utils";

const inputClassName =
  "h-9 w-full rounded-md border border-[#e8ecf2] bg-white px-3 text-[13px] text-[#111827] shadow-none focus-visible:ring-1 focus-visible:ring-[#2563eb]";

function tabFromSearch(value: string | null): ProfileUpdateRequestTab {
  return value === "status" ? "status" : "request";
}

export function StudentProfileUpdateRequestsScreen() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const profile = useStudentProfile();
  const academics = useAcademicDetails();
  const history = useProfileCorrections();
  const submit = useSubmitProfileCorrection();

  const [tab, setTab] = useState<ProfileUpdateRequestTab>(() => tabFromSearch(searchParams.get("tab")));

  const initialField = useMemo(() => {
    const raw = searchParams.get("field")?.trim() ?? "";
    return isProfileCorrectionFieldName(raw) ? raw : "";
  }, [searchParams]);

  const [fieldName, setFieldName] = useState<ProfileCorrectionFieldName | "">("");
  const [proposedValue, setProposedValue] = useState("");
  const [reason, setReason] = useState("");
  const [formMessage, setFormMessage] = useState<{ tone: "ok" | "err"; text: string } | null>(null);
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);

  useEffect(() => {
    setTab(tabFromSearch(searchParams.get("tab")));
  }, [searchParams]);

  useEffect(() => {
    if (initialField) {
      setFieldName(initialField);
      setTab("request");
    }
  }, [initialField]);

  useEffect(() => {
    const rows = history.data;
    if (!rows?.length) {
      setSelectedRequestId(null);
      return;
    }
    setSelectedRequestId((prev) =>
      prev && rows.some((r) => r.request_id === prev) ? prev : rows[0]!.request_id,
    );
  }, [history.data]);

  function setTabWithUrl(next: ProfileUpdateRequestTab) {
    setTab(next);
    const params = new URLSearchParams(searchParams.toString());
    if (next === "status") params.set("tab", "status");
    else params.delete("tab");
    const qs = params.toString();
    router.replace(qs ? `/student/profile/update-requests?${qs}` : "/student/profile/update-requests");
  }

  function resetForm(keepField = false) {
    if (!keepField) setFieldName("");
    setProposedValue("");
    setReason("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormMessage(null);
    if (!fieldName) {
      setFormMessage({ tone: "err", text: "Select a field to change." });
      return;
    }
    if (proposedValue.trim().length < 1) {
      setFormMessage({ tone: "err", text: "Enter the requested value." });
      return;
    }
    if (reason.trim().length < 3) {
      setFormMessage({ tone: "err", text: "Add a reason (at least 3 characters)." });
      return;
    }

    submit.mutate(
      {
        field_name: fieldName,
        proposed_value: proposedValue.trim(),
        reason: reason.trim(),
      },
      {
        onSuccess: (data) => {
          setFormMessage({
            tone: "ok",
            text: `Request ${formatRequestReference(data.request_id)} submitted. College admin will review it.`,
          });
          resetForm(true);
          void history.refetch();
          setTabWithUrl("status");
        },
        onError: (err) => {
          setFormMessage({
            tone: "err",
            text: err instanceof Error ? err.message : "Could not submit request.",
          });
        },
      },
    );
  }

  const currentValue =
    fieldName && profile.data
      ? profileCorrectionCurrentValue(fieldName, profile.data, academics.data)
      : "";

  const selectedHelper = PROFILE_CORRECTION_FIELD_OPTIONS.find((o) => o.value === fieldName)?.helper;

  const selectedRow = history.data?.find((r) => r.request_id === selectedRequestId) ?? null;

  const heading =
    tab === "request"
      ? {
          title: "Profile update request",
          description: "Request a correction to locked official fields",
          figmaNode: "164:2274",
        }
      : {
          title: "Profile update request status",
          description: "Track your requests",
          figmaNode: "164:2603",
        };

  return (
    <div className="space-y-5" data-figma-node={heading.figmaNode}>
      <ProfilePageHeading
        title={heading.title}
        description={heading.description}
        backHref="/student/profile"
        actions={
          tab === "request" ? (
            <>
              <button
                type="button"
                onClick={() => {
                  resetForm();
                  setFormMessage(null);
                }}
                className={STUDENT_BTN_OUTLINE}
              >
                <CollegeAdminIcon name="x" size={14} />
                Cancel
              </button>
              <button
                type="submit"
                form="profile-correction-form"
                className={STUDENT_BTN_PRIMARY}
                disabled={submit.isPending || !profile.data}
              >
                <CollegeAdminIcon name="send" size={14} className="text-white" />
                {submit.isPending ? "Submitting…" : "Submit request"}
              </button>
            </>
          ) : (
            <button type="button" onClick={() => setTabWithUrl("request")} className={STUDENT_BTN_PRIMARY}>
              <CollegeAdminIcon name="plus" size={14} className="text-white" />
              New request
            </button>
          )
        }
      />

      <ProfileUpdateRequestTabs value={tab} onChange={setTabWithUrl} />

      {tab === "request" ? (
        <div className="grid items-start gap-6 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <ProfilePanel title="Request" figmaNode="164:2527">
              <form
                id="profile-correction-form"
                className="space-y-4"
                onSubmit={(e) => void handleSubmit(e)}
              >
                <ProfileFormField label="Field to change *">
                  <select
                    className={cn(inputClassName, "appearance-none")}
                    value={fieldName}
                    onChange={(e) => {
                      const next = e.target.value;
                      setFieldName(isProfileCorrectionFieldName(next) ? next : "");
                      setProposedValue("");
                    }}
                  >
                    <option value="">Select field…</option>
                    <optgroup label="Personal">
                      {PROFILE_CORRECTION_FIELD_OPTIONS.filter((o) => o.group === "personal").map(
                        (opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ),
                      )}
                    </optgroup>
                    <optgroup label="Academic">
                      {PROFILE_CORRECTION_FIELD_OPTIONS.filter((o) => o.group === "academic").map(
                        (opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ),
                      )}
                    </optgroup>
                    <optgroup label="Guardian">
                      {PROFILE_CORRECTION_FIELD_OPTIONS.filter((o) => o.group === "guardian").map(
                        (opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ),
                      )}
                    </optgroup>
                  </select>
                  {selectedHelper ? (
                    <span className="mt-1 block text-[11px] text-[#607086]">{selectedHelper}</span>
                  ) : null}
                </ProfileFormField>

                <ProfileFormField label="Current value">
                  <div className="relative">
                    <Input
                      readOnly
                      value={currentValue || "—"}
                      className={cn(inputClassName, "bg-[#f8fafc] pr-9 text-[#607086]")}
                    />
                    <CollegeAdminIcon
                      name="lock"
                      size={13}
                      className="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 text-[#8a98aa]"
                    />
                  </div>
                </ProfileFormField>

                <ProfileFormField label="Requested value *">
                  <Input
                    value={proposedValue}
                    onChange={(e) => setProposedValue(e.target.value)}
                    placeholder="Value as it should appear after approval"
                    maxLength={500}
                    className={inputClassName}
                  />
                </ProfileFormField>

                <ProfileFormField label="Reason *">
                  <textarea
                    className="min-h-[76px] w-full rounded-md border border-[#dce3ec] bg-white px-3 py-2 text-[13px] text-[#172b45] focus-visible:ring-1 focus-visible:ring-[#245dd8]"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Why this correction is needed"
                    maxLength={2000}
                  />
                </ProfileFormField>

                {formMessage ? (
                  <p
                    className={cn(
                      "text-[13px]",
                      formMessage.tone === "ok" ? "text-[#047857]" : "text-[#b91c1c]",
                    )}
                  >
                    {formMessage.text}
                  </p>
                ) : null}

                <p className="text-[11px] text-[#8a98aa]">
                  Contact details and addresses update immediately on{" "}
                  <Link href="/student/profile/edit" className="font-semibold text-[#245dd8] hover:underline">
                    Edit permitted fields
                  </Link>
                  .
                </p>
              </form>
            </ProfilePanel>
          </div>

          <div className="lg:col-span-2">
            <ProfilePanel title="What happens next" figmaNode="164:2575">
              <ul className="space-y-0 text-[13px] text-[#172b45]">
                <WorkflowStep
                  icon="user"
                  title="Department review"
                  detail="Usually within 2 working days"
                />
                <WorkflowStep
                  icon="file-check"
                  title="College admin approval"
                  detail="Usually within 3 working days"
                />
                <WorkflowStep icon="check" title="Record updated" detail="You will be notified" />
              </ul>
            </ProfilePanel>
          </div>
        </div>
      ) : (
        <QueryState
          query={history}
          isLoading={history.isLoading}
          isError={history.isError}
          error={history.error}
          onRetry={() => void history.refetch()}
          isEmpty={!history.data?.length}
          emptyMessage="No correction requests yet. Submit a new request when official data needs to change."
        >
          {history.data?.length ? (
            <div className="grid items-start gap-6 lg:grid-cols-5">
              <div className="lg:col-span-3">
                <ProfilePanel
                  title="Your requests"
                  action={
                    <span className="text-[11px] font-normal text-[#8a98aa]">
                      {history.data.length} request{history.data.length === 1 ? "" : "s"}
                    </span>
                  }
                >
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[520px] text-left text-[12px]">
                      <thead>
                        <tr className="border-b border-[#eef2f6] text-[11px] font-semibold text-[#8a98aa]">
                          <th className="pb-2 pr-3 font-semibold">Request</th>
                          <th className="pb-2 pr-3 font-semibold">Field</th>
                          <th className="pb-2 pr-3 font-semibold">Submitted</th>
                          <th className="pb-2 pr-3 font-semibold">Approver</th>
                          <th className="pb-2 font-semibold">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history.data.map((row) => (
                          <tr
                            key={row.request_id}
                            className={cn(
                              "cursor-pointer border-b border-[#f1f5f9] transition-colors last:border-0",
                              selectedRequestId === row.request_id && "bg-[#f8fafc]",
                            )}
                            onClick={() => setSelectedRequestId(row.request_id)}
                          >
                            <td className="py-3 pr-3 font-medium text-[#172b45]">
                              {formatRequestReference(row.request_id, row.created_at)}
                            </td>
                            <td className="py-3 pr-3 text-[#374151]">
                              {profileCorrectionFieldLabel(row.field_name)}
                            </td>
                            <td className="py-3 pr-3 text-[#607086]">
                              {formatSubmittedShort(row.created_at)}
                            </td>
                            <td className="py-3 pr-3 text-[#607086]">
                              {profileCorrectionFieldApprover(row.field_name)}
                            </td>
                            <td className="py-3">
                              <CorrectionStatusBadge status={row.status} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </ProfilePanel>
              </div>

              <div className="lg:col-span-2">
                {selectedRow ? (
                  <RequestDetailPanels row={selectedRow} />
                ) : (
                  <ProfilePanel title="Request timeline">
                    <p className="text-[12px] text-[#607086]">Select a request to view progress.</p>
                  </ProfilePanel>
                )}
              </div>
            </div>
          ) : null}
        </QueryState>
      )}
    </div>
  );
}

function WorkflowStep({
  icon,
  title,
  detail,
}: {
  icon: "user" | "file-check" | "check";
  title: string;
  detail: string;
}) {
  return (
    <li className="flex gap-3 border-b border-[#eef2f6] py-3 last:border-0">
      <CollegeAdminIcon name={icon} size={18} className="mt-0.5 shrink-0 text-[#245dd8]" />
      <div>
        <p className="font-medium text-[#172b45]">{title}</p>
        <p className="mt-0.5 text-[11px] text-[#607086]">{detail}</p>
      </div>
    </li>
  );
}

function CorrectionStatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const label =
    normalized === "approved"
      ? "Approved"
      : normalized === "rejected"
        ? "Rejected"
        : normalized === "under_review"
          ? "Under review"
          : "Under review";
  const styles =
    normalized === "approved"
      ? "bg-[#e7f6ed] text-[#1f7a45]"
      : normalized === "rejected"
        ? "bg-[#fde8e8] text-[#b91c1c]"
        : "bg-[#fff4e5] text-[#b45309]";
  const dot =
    normalized === "approved"
      ? "bg-[#1f7a45]"
      : normalized === "rejected"
        ? "bg-[#b91c1c]"
        : "bg-[#b45309]";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-semibold",
        styles,
      )}
    >
      <span className={cn("size-1.5 rounded-full", dot)} aria-hidden />
      {label}
    </span>
  );
}

function RequestDetailPanels({ row }: { row: ProfileCorrectionRead }) {
  return (
    <div className="space-y-4">
      <ProfilePanel title="Request timeline">
        <RequestTimeline status={row.status} createdAt={row.created_at} updatedAt={row.updated_at} />
      </ProfilePanel>
      <ProfilePanel title="Details">
        <dl className="space-y-2 text-[12px]">
          <div>
            <dt className="text-[#8a98aa]">Requested value</dt>
            <dd className="font-medium text-[#172b45]">{row.proposed_value || "—"}</dd>
          </div>
          <div>
            <dt className="text-[#8a98aa]">Reason</dt>
            <dd className="text-[#374151]">{row.reason || "—"}</dd>
          </div>
          <div>
            <dt className="text-[#8a98aa]">Last updated</dt>
            <dd className="text-[#607086]">{formatDateTime(row.updated_at)}</dd>
          </div>
        </dl>
      </ProfilePanel>
    </div>
  );
}

function RequestTimeline({
  status,
  createdAt,
  updatedAt,
}: {
  status: string;
  createdAt: string;
  updatedAt: string;
}) {
  const s = status.toLowerCase();
  const approved = s === "approved";
  const rejected = s === "rejected";
  const inReview = !approved && !rejected;

  const steps = [
    {
      label: "Submitted",
      detail: formatSubmittedShort(createdAt),
      state: "done" as const,
    },
    {
      label: "Department review",
      detail: inReview ? "In progress" : approved ? "Completed" : rejected ? "Closed" : "—",
      state: inReview ? ("active" as const) : approved ? ("done" as const) : rejected ? ("muted" as const) : ("done" as const),
    },
    {
      label: "College approval",
      detail: approved ? formatSubmittedShort(updatedAt) : rejected ? "Not approved" : "Pending",
      state: approved ? ("done" as const) : rejected ? ("muted" as const) : ("pending" as const),
    },
    {
      label: "Record updated",
      detail: approved ? "Completed" : "Pending",
      state: approved ? ("done" as const) : ("pending" as const),
    },
  ];

  return (
    <ol className="space-y-4">
      {steps.map((step) => (
        <li key={step.label} className="flex gap-3">
          <span
            className={cn(
              "mt-1 size-2.5 shrink-0 rounded-full",
              step.state === "done" && "bg-[#1f7a45]",
              step.state === "active" && "bg-[#b45309]",
              step.state === "pending" && "bg-[#dce3ec]",
              step.state === "muted" && "bg-[#cbd5e1]",
            )}
            aria-hidden
          />
          <div>
            <p className="text-[13px] font-medium text-[#172b45]">{step.label}</p>
            <p className="text-[11px] text-[#607086]">{step.detail}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

function formatSubmittedShort(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
}

function formatRequestReference(requestId: string, createdAt?: string): string {
  const suffix = requestId.replace(/^pfc_/, "").slice(0, 3).toUpperCase() || "000";
  if (createdAt) {
    const d = new Date(createdAt);
    if (!Number.isNaN(d.getTime())) {
      const mm = String(d.getMonth() + 1).padStart(2, "0");
      const dd = String(d.getDate()).padStart(2, "0");
      return `PUR-${mm}${dd}-${suffix}`;
    }
  }
  return requestId.toUpperCase();
}