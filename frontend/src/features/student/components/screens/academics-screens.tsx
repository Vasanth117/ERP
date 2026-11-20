"use client";

import { useState, type ChangeEvent, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DetailRow,
  PageHeading,
  QueryState,
  SectionPanel,
  StatusBadge,
  formatDateTime,
  toneForStatus,
} from "@/features/student/components/ui/student-screen-ui";
import { screenBySlug } from "@/features/student/config/screens";
import {
  useAcademicDetails,
  useAcademicEligibility,
  useEnrollmentHistory,
  useEnrollmentRequests,
  useEnrollmentStatus,
  useSubmitEnrollmentRequest,
} from "@/features/student/hooks/use-student-academics";

type AcademicsSlug =
  | "academics"
  | "enrollment-status"
  | "enrollment-history"
  | "academic-eligibility"
  | "enrollment-requests"
  | "new-enrollment-request";

export function AcademicsScreen({ slug }: { slug: AcademicsSlug }) {
  const def = screenBySlug(slug);
  return (
    <div>
      <PageHeading
        title={def?.title ?? "Academics"}
        description={def?.description}
        figmaPage="ST 02"
      />
      <AcademicsBody slug={slug} />
    </div>
  );
}

function AcademicsBody({ slug }: { slug: AcademicsSlug }) {
  switch (slug) {
    case "academics":
      return <AcademicsOverview />;
    case "enrollment-status":
      return <EnrollmentStatusView />;
    case "enrollment-history":
      return <EnrollmentHistoryView />;
    case "academic-eligibility":
      return <EligibilityView />;
    case "enrollment-requests":
      return <EnrollmentRequestsView />;
    case "new-enrollment-request":
      return <NewEnrollmentRequestView />;
    default:
      return null;
  }
}

function AcademicsOverview() {
  const academics = useAcademicDetails();
  return (
    <QueryState
      isLoading={academics.isLoading}
      isError={academics.isError}
      error={academics.error}
      onRetry={() => void academics.refetch()}
    >
      {academics.data ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <SectionPanel title="Admission">
            <DetailRow label="Programme" value={academics.data.admission.programme_name} />
            <DetailRow label="Department" value={academics.data.admission.department_name} />
            <DetailRow label="Batch / Section" value={`${academics.data.admission.batch_label ?? "—"} / ${academics.data.admission.section_code ?? "—"}`} />
          </SectionPanel>
          <SectionPanel title="Current enrollments">
            {academics.data.current_enrollments.length === 0 ? (
              <p className="text-sm text-[#9ca3af]">No active enrollment lines.</p>
            ) : (
              <ul className="divide-y divide-[#f1f5f9]">
                {academics.data.current_enrollments.map((line) => (
                  <li key={`${line.course_code}-${line.section_code}`} className="flex justify-between py-3 text-sm">
                    <span>
                      <span className="font-medium">{line.course_code}</span> · {line.course_name}
                    </span>
                    <StatusBadge label={line.status} tone={toneForStatus(line.status)} />
                  </li>
                ))}
              </ul>
            )}
          </SectionPanel>
        </div>
      ) : null}
    </QueryState>
  );
}

function EnrollmentStatusView() {
  const status = useEnrollmentStatus();
  return (
    <SectionPanel title="Enrollment standing">
      <QueryState
        isLoading={status.isLoading}
        isError={status.isError}
        error={status.error}
        onRetry={() => void status.refetch()}
      >
        {status.data ? (
          <div className="grid gap-0 sm:grid-cols-2">
            <DetailRow label="Academic year" value={status.data.academic_year_label} />
            <DetailRow label="Semester" value={status.data.semester_label} />
            <DetailRow
              label="Enrollment status"
              value={<StatusBadge label={status.data.enrollment_status} tone={toneForStatus(status.data.enrollment_status)} />}
            />
            <DetailRow
              label="Academic standing"
              value={<StatusBadge label={status.data.academic_standing} tone={toneForStatus(status.data.academic_standing)} />}
            />
            <DetailRow
              label="Progression"
              value={<StatusBadge label={status.data.progression_status} tone={toneForStatus(status.data.progression_status)} />}
            />
          </div>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function EnrollmentHistoryView() {
  const history = useEnrollmentHistory(50, 0);
  return (
    <SectionPanel title="Past terms">
      <QueryState
        isLoading={history.isLoading}
        isError={history.isError}
        error={history.error}
        onRetry={() => void history.refetch()}
        isEmpty={!history.data?.items.length}
        emptyMessage="No closed enrollment history."
      >
        {history.data ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-xs uppercase text-[#9ca3af]">
                <tr>
                  <th className="px-2 py-2">Term</th>
                  <th className="px-2 py-2">Standing</th>
                  <th className="px-2 py-2">Credits</th>
                  <th className="px-2 py-2">CGPA</th>
                  <th className="px-2 py-2">Closed</th>
                </tr>
              </thead>
              <tbody>
                {history.data.items.map((row) => (
                  <tr key={row.id} className="border-t border-[#f1f5f9]">
                    <td className="px-2 py-3">
                      {row.academic_year_label} · {row.semester_label}
                    </td>
                    <td className="px-2 py-3 capitalize">{row.final_standing.replace(/_/g, " ")}</td>
                    <td className="px-2 py-3">{row.credits_earned}</td>
                    <td className="px-2 py-3">{row.cgpa ?? "—"}</td>
                    <td className="px-2 py-3 text-xs text-[#9ca3af]">{formatDateTime(row.closed_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function EligibilityView() {
  const eligibility = useAcademicEligibility();
  return (
    <SectionPanel title="Eligibility snapshot">
      <QueryState
        isLoading={eligibility.isLoading}
        isError={eligibility.isError}
        error={eligibility.error}
        onRetry={() => void eligibility.refetch()}
      >
        {eligibility.data ? (
          <div className="grid gap-0 sm:grid-cols-2">
            <DetailRow
              label="Promotion eligible"
              value={
                eligibility.data.promotion_eligible == null
                  ? "—"
                  : eligibility.data.promotion_eligible
                    ? "Yes"
                    : "No"
              }
            />
            <DetailRow label="Credits registered" value={eligibility.data.credits_registered} />
            <DetailRow label="Credits earned" value={eligibility.data.credits_earned} />
            <DetailRow label="CGPA" value={eligibility.data.cgpa ?? "—"} />
          </div>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function EnrollmentRequestsView() {
  const requests = useEnrollmentRequests(50, 0);
  return (
    <SectionPanel title="Your requests">
      <QueryState
        isLoading={requests.isLoading}
        isError={requests.isError}
        error={requests.error}
        onRetry={() => void requests.refetch()}
        isEmpty={!requests.data?.items.length}
        emptyMessage="No enrollment requests submitted."
      >
        {requests.data ? (
          <ul className="divide-y divide-[#f1f5f9]">
            {requests.data.items.map((req) => (
              <li key={req.id} className="py-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-medium text-[#111827]">{req.title}</p>
                  <StatusBadge label={req.status} tone={toneForStatus(req.status)} />
                </div>
                <p className="mt-1 text-sm text-[#6b7280]">{req.description}</p>
                <p className="mt-2 text-xs text-[#9ca3af]">
                  {req.request_type.replace(/_/g, " ")} · Submitted {formatDateTime(req.submitted_at)}
                </p>
                {req.reviewer_note ? (
                  <p className="mt-2 text-xs text-[#607086]">Note: {req.reviewer_note}</p>
                ) : null}
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function NewEnrollmentRequestView() {
  const submit = useSubmitEnrollmentRequest();
  const [requestType, setRequestType] = useState("enrollment_change");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);

  return (
    <SectionPanel title="Submit request">
      <form
        className="max-w-xl space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          submit.mutate(
            { request_type: requestType, title, description },
            {
              onSuccess: () => {
                setFeedback("Request submitted.");
                setTitle("");
                setDescription("");
              },
              onError: (err) =>
                setFeedback(err instanceof Error ? err.message : "Submission failed"),
            },
          );
        }}
      >
        <FormField label="Request type">
          <Input value={requestType} onChange={(ev) => setRequestType(ev.target.value)} required />
        </FormField>
        <FormField label="Title">
          <Input value={title} onChange={(ev) => setTitle(ev.target.value)} required maxLength={200} />
        </FormField>
        <FormField label="Description">
          <textarea
            className="min-h-28 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={description}
            onChange={(ev: ChangeEvent<HTMLTextAreaElement>) => setDescription(ev.target.value)}
            required
            minLength={10}
            rows={5}
          />
        </FormField>
        <Button type="submit" disabled={submit.isPending} className="bg-[#245dd8]">
          {submit.isPending ? "Submitting…" : "Submit request"}
        </Button>
        {feedback ? <p className="text-sm text-[#6b7280]">{feedback}</p> : null}
      </form>
    </SectionPanel>
  );
}

function FormField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-xs font-medium text-[#6b7280]">{label}</span>
      {children}
    </label>
  );
}