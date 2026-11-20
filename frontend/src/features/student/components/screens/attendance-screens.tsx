"use client";

import { useState, type ChangeEvent } from "react";

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
import { DateAnchorField } from "@/features/student/components/screens/shared-tables";
import {
  useAttendanceEligibility,
  useAttendanceExport,
  useAttendanceHistory,
  useAttendanceShortages,
  useAttendanceSummary,
  useDailyAttendance,
  useDiscrepancyRequests,
  useSubjectAttendance,
  useSubmitDiscrepancyRequest,
} from "@/features/student/hooks/use-student-attendance";

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export type AttendanceSlug =
  | "attendance"
  | "attendance-subjects"
  | "attendance-daily"
  | "attendance-history"
  | "attendance-shortages"
  | "attendance-eligibility"
  | "attendance-export"
  | "discrepancy-requests"
  | "new-discrepancy-request";

export function AttendanceScreen({ slug }: { slug: AttendanceSlug }) {
  const def = screenBySlug(slug);
  return (
    <div>
      <PageHeading title={def?.title ?? "Attendance"} description={def?.description} figmaPage="ST 06" />
      <AttendanceBody slug={slug} />
    </div>
  );
}

function AttendanceBody({ slug }: { slug: AttendanceSlug }) {
  switch (slug) {
    case "attendance":
      return <AttendanceHub />;
    case "attendance-subjects":
      return <SubjectsView />;
    case "attendance-daily":
      return <DailyView />;
    case "attendance-history":
      return <HistoryView />;
    case "attendance-shortages":
      return <ShortagesView />;
    case "attendance-eligibility":
      return <EligibilityView />;
    case "attendance-export":
      return <ExportView />;
    case "discrepancy-requests":
      return <DiscrepancyListView />;
    case "new-discrepancy-request":
      return <NewDiscrepancyView />;
    default:
      return null;
  }
}

function AttendanceHub() {
  const summary = useAttendanceSummary();
  const shortages = useAttendanceShortages();
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <SectionPanel title="Semester summary">
        <QueryState isLoading={summary.isLoading} isError={summary.isError} error={summary.error} onRetry={() => void summary.refetch()}>
          {summary.data ? (
            <>
              <DetailRow label="Overall" value={summary.data.overall_percentage != null ? `${summary.data.overall_percentage.toFixed(1)}%` : "—"} />
              <DetailRow label="Minimum required" value={`${summary.data.min_required}%`} />
              <DetailRow label="Data status" value={summary.data.data_status} />
            </>
          ) : null}
        </QueryState>
      </SectionPanel>
      <SectionPanel title="Shortage warnings">
        <QueryState isLoading={shortages.isLoading} isError={shortages.isError} error={shortages.error} onRetry={() => void shortages.refetch()} isEmpty={!shortages.data?.length}>
          {shortages.data ? (
            <ul className="divide-y divide-[#f1f5f9] text-sm">
              {shortages.data.map((s) => (
                <li key={`${s.course_code}-${s.section}`} className="py-2">
                  {s.course_code} · {s.percentage ?? "—"}% (min {s.min_required}%)
                </li>
              ))}
            </ul>
          ) : null}
        </QueryState>
      </SectionPanel>
    </div>
  );
}

function SubjectsView() {
  const subjects = useSubjectAttendance();
  return (
    <SectionPanel title="Subject-wise attendance">
      <QueryState isLoading={subjects.isLoading} isError={subjects.isError} error={subjects.error} onRetry={() => void subjects.refetch()} isEmpty={!subjects.data?.length}>
        {subjects.data ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead className="text-xs uppercase text-[#9ca3af]">
                <tr>
                  <th className="px-2 py-2">Course</th>
                  <th className="px-2 py-2">%</th>
                  <th className="px-2 py-2">Sessions</th>
                  <th className="px-2 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {subjects.data.map((row) => (
                  <tr key={`${row.course_code}-${row.section}`} className="border-t border-[#f1f5f9]">
                    <td className="px-2 py-3">{row.course_code}</td>
                    <td className="px-2 py-3">{row.percentage ?? "—"}</td>
                    <td className="px-2 py-3">
                      {row.sessions_recorded}/{row.sessions_held}
                    </td>
                    <td className="px-2 py-3">{row.data_status}</td>
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

function DailyView() {
  const [date, setDate] = useState(todayIso());
  const daily = useDailyAttendance(date);
  return (
    <SectionPanel title="Daily marks">
      <DateAnchorField value={date} onChange={setDate} label="Session date" />
      <QueryState isLoading={daily.isLoading} isError={daily.isError} error={daily.error} onRetry={() => void daily.refetch()} isEmpty={!daily.data?.length}>
        {daily.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {daily.data.map((m) => (
              <li key={m.session_id} className="flex justify-between py-3">
                <span>
                  {m.course_code} · {m.session_date}
                </span>
                <StatusBadge label={m.status ?? "unknown"} tone={toneForStatus(m.status ?? "")} />
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function HistoryView() {
  const history = useAttendanceHistory(50, 0);
  return (
    <SectionPanel title="Attendance history">
      <QueryState isLoading={history.isLoading} isError={history.isError} error={history.error} onRetry={() => void history.refetch()} isEmpty={!history.data?.items.length}>
        {history.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {history.data.items.map((m) => (
              <li key={`${m.session_id}-${m.session_date}`} className="py-2">
                {m.session_date} · {m.course_code} · {m.status ?? "—"}
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function ShortagesView() {
  const shortages = useAttendanceShortages();
  return (
    <SectionPanel title="Shortage details">
      <QueryState isLoading={shortages.isLoading} isError={shortages.isError} error={shortages.error} onRetry={() => void shortages.refetch()} isEmpty={!shortages.data?.length}>
        {shortages.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {shortages.data.map((s) => (
              <li key={`${s.course_code}-${s.section}`} className="py-3">
                <p className="font-medium">{s.course_code}</p>
                <p className="text-xs text-[#6b7280]">
                  {s.percentage ?? "—"}% · need {s.min_required}% · sessions to clear:{" "}
                  {s.sessions_remaining_to_clear ?? "—"}
                </p>
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function EligibilityView() {
  const eligibility = useAttendanceEligibility();
  return (
    <SectionPanel title="Exam / activity eligibility">
      <QueryState isLoading={eligibility.isLoading} isError={eligibility.isError} error={eligibility.error} onRetry={() => void eligibility.refetch()}>
        {eligibility.data ? (
          <>
            <DetailRow label="Eligible" value={eligibility.data.eligible ? "Yes" : "No"} />
            <DetailRow label="Overall %" value={eligibility.data.overall_percentage ?? "—"} />
            <DetailRow label="Min required" value={eligibility.data.min_required} />
            {eligibility.data.reasons.length > 0 ? (
              <ul className="mt-3 list-disc pl-5 text-sm text-[#4b5563]">
                {eligibility.data.reasons.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            ) : null}
          </>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function ExportView() {
  const exp = useAttendanceExport();
  return (
    <SectionPanel title="Export summary (CSV)">
      <p className="mb-4 text-sm text-[#6b7280]">Downloads the payload from GET /students/me/attendance/export.</p>
      <Button
        type="button"
        className="bg-[#245dd8]"
        disabled={exp.isFetching}
        onClick={() => {
          void exp.refetch().then((res) => {
            const data = res.data;
            if (!data?.csv_content) return;
            const blob = new Blob([data.csv_content], { type: "text/csv" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `attendance-${data.academic_year_label}-${data.semester_label}.csv`;
            a.click();
            URL.revokeObjectURL(url);
          });
        }}
      >
        {exp.isFetching ? "Generating…" : "Download CSV"}
      </Button>
      {exp.isError ? <p className="mt-2 text-sm text-red-700">{exp.error?.message}</p> : null}
    </SectionPanel>
  );
}

function DiscrepancyListView() {
  const list = useDiscrepancyRequests(50, 0);
  return (
    <SectionPanel title="Discrepancy requests">
      <QueryState isLoading={list.isLoading} isError={list.isError} error={list.error} onRetry={() => void list.refetch()} isEmpty={!list.data?.items.length}>
        {list.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {list.data.items.map((r) => (
              <li key={r.id} className="py-3">
                <DiscrepancyRow r={r} />
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function DiscrepancyRow({ r }: { r: { course_code: string; session_date: string; claimed_status: string; status: string; submitted_at: string } }) {
  return (
    <>
      <p className="font-medium">
        {r.course_code} · {r.session_date}
      </p>
      <p className="text-xs text-[#6b7280]">
        Claimed {r.claimed_status} · <StatusBadge label={r.status} tone={toneForStatus(r.status)} />
      </p>
      <p className="text-[10px] text-[#9ca3af]">{formatDateTime(r.submitted_at)}</p>
    </>
  );
}

function NewDiscrepancyView() {
  const submit = useSubmitDiscrepancyRequest();
  const [sessionId, setSessionId] = useState("");
  const [claimed, setClaimed] = useState("present");
  const [reason, setReason] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  return (
    <SectionPanel title="Submit discrepancy">
      <form
        className="max-w-lg space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          submit.mutate(
            { session_id: sessionId, claimed_status: claimed, reason },
            {
              onSuccess: () => {
                setMsg("Request submitted.");
                setSessionId("");
                setReason("");
              },
              onError: (err) => setMsg(err instanceof Error ? err.message : "Failed"),
            },
          );
        }}
      >
        <label className="block text-sm">
          <span className="mb-1 block text-xs text-[#6b7280]">Session ID</span>
          <Input value={sessionId} onChange={(e) => setSessionId(e.target.value)} required />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-xs text-[#6b7280]">Claimed status</span>
          <select
            className="h-10 w-full rounded-lg border border-[#dce3ec] px-3"
            value={claimed}
            onChange={(e) => setClaimed(e.target.value)}
          >
            {["present", "absent", "late", "excused", "on_duty"].map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-xs text-[#6b7280]">Reason</span>
          <textarea
            className="min-h-24 w-full rounded-md border border-input px-3 py-2 text-sm"
            value={reason}
            onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setReason(e.target.value)}
            required
            minLength={10}
          />
        </label>
        <Button type="submit" disabled={submit.isPending} className="bg-[#245dd8]">
          Submit
        </Button>
        {msg ? <p className="text-sm text-[#6b7280]">{msg}</p> : null}
      </form>
    </SectionPanel>
  );
}