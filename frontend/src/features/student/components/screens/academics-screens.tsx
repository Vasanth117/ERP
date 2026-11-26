"use client";

import Link from "next/link";
import { useState, type ChangeEvent, type ReactNode } from "react";

import { PlusIcon } from "@/components/icons/erp/generated/plus";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AcademicOverviewScreen } from "@/features/student/components/screens/academic-overview-screen";
import { StudentEnrollmentDetailsScreen } from "@/features/student/components/screens/enrollment-details-screen";
import { ProgrammeDepartmentScreen } from "@/features/student/components/screens/programme-department-screen";
import { StudentAcademicStatusScreen } from "@/features/student/components/screens/student-academic-status-screen";
import { StudentSemestersScreen } from "@/features/student/components/screens/student-semesters-screen";
import { StudentSubjectsCreditsScreen } from "@/features/student/components/screens/student-subjects-credits-screen";
import {
  QueryState,
  formatDateTime,
} from "@/features/student/components/ui/student-screen-ui";
import {
  useEnrollmentHistory,
  useEnrollmentRequests,
  useSubmitEnrollmentRequest,
} from "@/features/student/hooks/use-student-academics";
import { cn } from "@/lib/utils";

type AcademicsSlug =
  | "academics"
  | "enrollment-status"
  | "enrollment-history"
  | "academic-eligibility"
  | "enrollment-details"
  | "enrollment-requests"
  | "new-enrollment-request"
  | "programme-department";

function StatusPill({
  label,
  tone = "muted",
}: {
  label: string;
  tone?: "success" | "warning" | "error" | "info" | "muted";
}) {
  const styles: Record<string, string> = {
    success: "bg-[#ecfdf5] text-[#047857]",
    warning: "bg-[#fff7ed] text-[#c2410c]",
    error: "bg-[#fef2f2] text-[#b91c1c]",
    info: "bg-[#eff6ff] text-[#1d4ed8]",
    muted: "bg-[#f3f4f6] text-[#6b7280]",
  };
  const dot: Record<string, string> = {
    success: "bg-[#10b981]",
    warning: "bg-[#f97316]",
    error: "bg-[#ef4444]",
    info: "bg-[#3b82f6]",
    muted: "bg-[#9ca3af]",
  };
  const key = tone in styles ? tone : "muted";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium capitalize",
        styles[key],
      )}
    >
      <span className={cn("size-1.5 rounded-full", dot[key])} aria-hidden />
      {label.replace(/_/g, " ")}
    </span>
  );
}

function SectionCard({
  title,
  action,
  children,
  footer,
  className,
}: {
  title: string;
  action?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]",
        className,
      )}
    >
      <div className="flex items-center justify-between border-b border-[#f1f5f9] px-5 py-4">
        <h2 className="text-[15px] font-semibold text-[#111827]">{title}</h2>
        {action ? <div>{action}</div> : null}
      </div>
      <div>{children}</div>
      {footer ? (
        <div className="border-t border-[#f1f5f9] px-5 py-3 text-[12px] font-medium text-[#6b7280]">
          {footer}
        </div>
      ) : null}
    </section>
  );
}

export function AcademicsScreen({ slug }: { slug: AcademicsSlug }) {
  if (slug === "academics") {
    return <AcademicOverviewScreen />;
  }

  return (
    <div className="space-y-6" data-figma-page="ST 02">
      <AcademicsBody slug={slug} />
    </div>
  );
}

function AcademicsBody({ slug }: { slug: AcademicsSlug }) {
  switch (slug) {
    case "enrollment-details":
      return <StudentEnrollmentDetailsScreen />;
    case "enrollment-status":
      return <StudentAcademicStatusScreen />;
    case "enrollment-history":
      return <StudentSemestersScreen />;
    case "academic-eligibility":
      return <StudentSubjectsCreditsScreen />;
    case "enrollment-requests":
      return <EnrollmentRequestsView />;
    case "new-enrollment-request":
      return <NewEnrollmentRequestView />;
    case "programme-department":
      return <ProgrammeDepartmentScreen />;
    default:
      return null;
  }
}

/* =========================================================================
   ST 02.03 - Semesters / Enrollment History View (Fixed 500 error & styled)
   ========================================================================= */
function EnrollmentHistoryView() {
  const { data, isLoading, isError, error, refetch } = useEnrollmentHistory(50, 0);

  const items = data?.items ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[26px] font-bold tracking-tight text-[#111827]">
          Enrollment History
        </h1>
        <p className="mt-1 text-[14px] text-[#6b7280]">
          Closed term summaries, registered courses, and historical credits earned
        </p>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        <SectionCard
          title="Past terms history"
          footer={items.length ? `${items.length} closed terms recorded` : undefined}
        >
          {items.length === 0 ? (
            <div className="py-12 text-center">
              <p className="text-sm font-medium text-[#111827]">No closed enrollment terms yet</p>
              <p className="mt-1 text-xs text-[#6b7280]">
                Historical term summaries will appear here once each academic semester is officially closed.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[48rem] text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#f1f5f9] text-[12px] font-medium text-[#6b7280]">
                    <th className="px-5 py-3 font-medium">Academic Year</th>
                    <th className="py-3 pr-3 font-medium">Semester</th>
                    <th className="py-3 pr-3 font-medium">Standing</th>
                    <th className="py-3 pr-3 font-medium">Credits Earned</th>
                    <th className="py-3 pr-3 font-medium">SGPA / CGPA</th>
                    <th className="py-3 pr-5 font-medium">Closed Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f1f5f9]">
                  {items.map((row) => (
                    <tr key={row.id} className="transition-colors hover:bg-[#f9fafb]">
                      <td className="px-5 py-3.5 font-medium text-[#111827]">
                        {row.academic_year_label}
                      </td>
                      <td className="py-3.5 pr-3 text-[#374151]">{row.semester_label}</td>
                      <td className="py-3.5 pr-3">
                        <StatusPill label={row.final_standing} tone="success" />
                      </td>
                      <td className="py-3.5 pr-3 tabular-nums font-semibold text-[#111827]">
                        {row.credits_earned}
                      </td>
                      <td className="py-3.5 pr-3 tabular-nums text-[#374151]">
                        {row.cgpa != null ? row.cgpa.toFixed(2) : "—"}
                      </td>
                      <td className="py-3.5 pr-5 text-[12px] text-[#6b7280]">
                        {formatDateTime(row.closed_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      </QueryState>
    </div>
  );
}

/* =========================================================================
   ST 02.05 - Enrollment Requests View
   ========================================================================= */
function EnrollmentRequestsView() {
  const { data, isLoading, isError, error, refetch } = useEnrollmentRequests(50, 0);

  const items = data?.items ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-[26px] font-bold tracking-tight text-[#111827]">
            Enrollment Requests
          </h1>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            Track submitted requests for section changes, course adjustments, and leaves
          </p>
        </div>
        <div>
          <Link
            href="/student/academics/new-enrollment-request"
            className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-[#2563eb] px-4 text-xs font-medium text-white shadow-sm transition-colors hover:bg-[#1d4ed8]"
          >
            <PlusIcon className="size-3.5" aria-hidden />
            <span>New request</span>
          </Link>
        </div>
      </div>

      <QueryState isLoading={isLoading} isError={isError} error={error} onRetry={() => void refetch()}>
        <SectionCard
          title="Submitted requests"
          footer={items.length ? `${items.length} requests on file` : undefined}
        >
          {items.length === 0 ? (
            <div className="py-12 text-center">
              <p className="text-sm font-medium text-[#111827]">No requests submitted yet</p>
              <p className="mt-1 text-xs text-[#6b7280]">
                Need to change a section or request a course adjustment? Click &quot;New request&quot; above.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[48rem] text-left text-[13px]">
                <thead>
                  <tr className="border-b border-[#f1f5f9] text-[12px] font-medium text-[#6b7280]">
                    <th className="px-5 py-3 font-medium">Type</th>
                    <th className="py-3 pr-3 font-medium">Title</th>
                    <th className="py-3 pr-3 font-medium">Term</th>
                    <th className="py-3 pr-3 font-medium">Status</th>
                    <th className="py-3 pr-3 font-medium">Submitted</th>
                    <th className="py-3 pr-5 font-medium">Reviewer Note</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f1f5f9]">
                  {items.map((req) => (
                    <tr key={req.id} className="transition-colors hover:bg-[#f9fafb]">
                      <td className="px-5 py-3.5 font-medium text-[#111827]">
                        {req.request_type.replace(/_/g, " ")}
                      </td>
                      <td className="py-3.5 pr-3 text-[#374151]">
                        <p className="font-medium text-[#111827]">{req.title}</p>
                        <p className="line-clamp-1 text-xs text-[#6b7280]">{req.description}</p>
                      </td>
                      <td className="py-3.5 pr-3 text-[#6b7280]">
                        {req.academic_year_label} · {req.semester_label}
                      </td>
                      <td className="py-3.5 pr-3">
                        <StatusPill
                          label={req.status}
                          tone={
                            req.status.toUpperCase() === "APPROVED"
                              ? "success"
                              : req.status.toUpperCase() === "REJECTED"
                                ? "error"
                                : "warning"
                          }
                        />
                      </td>
                      <td className="py-3.5 pr-3 text-[12px] text-[#6b7280]">
                        {formatDateTime(req.submitted_at)}
                      </td>
                      <td className="py-3.5 pr-5 text-[12px] text-[#4b5563]">
                        {req.reviewer_note || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      </QueryState>
    </div>
  );
}

/* =========================================================================
   ST 02.06 - New Request Form (Tuned to Department Admin style)
   ========================================================================= */
function NewEnrollmentRequestView() {
  const submit = useSubmitEnrollmentRequest();
  const [requestType, setRequestType] = useState("SECTION_CHANGE");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [feedback, setFeedback] = useState<{ message: string; isError?: boolean } | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[26px] font-bold tracking-tight text-[#111827]">
            Submit Academic Request
          </h1>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            Submit an official request for section changes, course adjustments, or academic leave
          </p>
        </div>
        <Link
          href="/student/academics/enrollment-requests"
          className="text-xs font-medium text-[#2563eb] hover:underline"
        >
          ← Back to requests
        </Link>
      </div>

      <SectionCard title="New request form" className="max-w-2xl">
        <form
          className="space-y-4 p-6"
          onSubmit={(e) => {
            e.preventDefault();
            submit.mutate(
              { request_type: requestType, title, description },
              {
                onSuccess: () => {
                  setFeedback({ message: "Request successfully submitted for administrative review." });
                  setTitle("");
                  setDescription("");
                },
                onError: (err) =>
                  setFeedback({
                    message: err instanceof Error ? err.message : "Submission failed",
                    isError: true,
                  }),
              },
            );
          }}
        >
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-[#374151]">
              Request Type
            </label>
            <select
              value={requestType}
              onChange={(e) => setRequestType(e.target.value)}
              className="mt-1.5 h-10 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px] text-[#374151] shadow-sm focus:border-[#2563eb] focus:outline-none"
            >
              <option value="SECTION_CHANGE">Section Change Request</option>
              <option value="COURSE_ADD">Course Add Request</option>
              <option value="COURSE_DROP">Course Drop Request</option>
              <option value="LEAVE_OF_ABSENCE">Leave of Absence</option>
              <option value="OTHER">Other Academic Request</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-[#374151]">
              Request Title
            </label>
            <Input
              value={title}
              onChange={(ev) => setTitle(ev.target.value)}
              placeholder="e.g. Request to change from Section A to Section B"
              required
              maxLength={200}
              className="mt-1.5 h-10 border-[#dce3ec]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-[#374151]">
              Detailed Reason &amp; Supporting Information
            </label>
            <textarea
              className="mt-1.5 min-h-32 w-full rounded-md border border-[#dce3ec] bg-white p-3 text-[13px] text-[#374151] shadow-sm focus:border-[#2563eb] focus:outline-none"
              value={description}
              onChange={(ev: ChangeEvent<HTMLTextAreaElement>) => setDescription(ev.target.value)}
              placeholder="State the academic reasons and specific circumstances for this request..."
              required
              minLength={10}
              rows={5}
            />
          </div>

          <div className="pt-2">
            <Button
              type="submit"
              disabled={submit.isPending}
              className="h-10 bg-[#2563eb] px-6 text-xs font-medium text-white hover:bg-[#1d4ed8]"
            >
              {submit.isPending ? "Submitting request…" : "Submit request"}
            </Button>
          </div>

          {feedback ? (
            <div
              className={cn(
                "rounded-md p-3 text-xs font-medium",
                feedback.isError
                  ? "bg-[#fef2f2] text-[#b91c1c]"
                  : "bg-[#ecfdf5] text-[#047857]",
              )}
            >
              {feedback.message}
            </div>
          ) : null}
        </form>
      </SectionCard>
    </div>
  );
}
