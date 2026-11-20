"use client";

import { useState } from "react";

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
  AssessmentIdPicker,
  useAssessmentIdFromQuery,
} from "@/features/student/components/screens/assessment-id-picker";
import { EventsList } from "@/features/student/components/screens/shared-tables";
import {
  useCiaComponents,
  useCiaCorrections,
  useCiaHistory,
  useCiaMarks,
  useCiaSchedules,
  useCiaSubjectMarks,
  useCiaSummary,
} from "@/features/student/hooks/use-student-cia";

export type CiaSlug =
  | "cia"
  | "cia-schedules"
  | "cia-marks"
  | "cia-subject-marks"
  | "cia-corrections"
  | "cia-history"
  | "cia-components";

export function CiaScreen({ slug }: { slug: CiaSlug }) {
  const def = screenBySlug(slug);
  return (
    <div>
      <PageHeading title={def?.title ?? "CIA Marks"} description={def?.description} figmaPage="ST 07" />
      <CiaBody slug={slug} />
    </div>
  );
}

function CiaBody({ slug }: { slug: CiaSlug }) {
  switch (slug) {
    case "cia":
      return <CiaHub />;
    case "cia-schedules":
      return <SchedulesView />;
    case "cia-marks":
      return <MarksView />;
    case "cia-subject-marks":
      return <SubjectMarksView />;
    case "cia-corrections":
      return <CorrectionsView />;
    case "cia-history":
      return <HistoryView />;
    case "cia-components":
      return <ComponentsView />;
    default:
      return null;
  }
}

function CiaHub() {
  const summary = useCiaSummary();
  const schedules = useCiaSchedules();
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <SectionPanel title="CIA summary">
        <QueryState isLoading={summary.isLoading} isError={summary.isError} error={summary.error} onRetry={() => void summary.refetch()}>
          {summary.data ? (
            <>
              <DetailRow label="Term" value={`${summary.data.academic_year_label} · ${summary.data.semester_label}`} />
              <DetailRow label="Published" value={summary.data.published_count} />
              <DetailRow label="Unpublished" value={summary.data.unpublished_count} />
              <DetailRow label="Missing" value={summary.data.missing_count} />
            </>
          ) : null}
        </QueryState>
      </SectionPanel>
      <SectionPanel title="Upcoming internal assessments">
        <QueryState isLoading={schedules.isLoading} isError={schedules.isError} error={schedules.error} onRetry={() => void schedules.refetch()} isEmpty={!schedules.data?.length}>
          {schedules.data ? (
            <EventsList
              items={schedules.data.map((s) => ({
                id: s.id,
                title: `${s.course_code} — ${s.title}`,
                description: s.assessment_type,
                event_at: s.scheduled_at,
              }))}
            />
          ) : null}
        </QueryState>
      </SectionPanel>
    </div>
  );
}

function SchedulesView() {
  const schedules = useCiaSchedules();
  return (
    <SectionPanel title="CIA schedules">
      <QueryState isLoading={schedules.isLoading} isError={schedules.isError} error={schedules.error} onRetry={() => void schedules.refetch()} isEmpty={!schedules.data?.length}>
        {schedules.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {schedules.data.map((s) => (
              <li key={s.id} className="py-3">
                <p className="font-medium">{s.title}</p>
                <p className="text-xs text-[#6b7280]">
                  {s.course_code} · {s.assessment_type} · {formatDateTime(s.scheduled_at)}
                </p>
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function MarksView() {
  const marks = useCiaMarks();
  return (
    <SectionPanel title="Published CIA marks">
      <QueryState isLoading={marks.isLoading} isError={marks.isError} error={marks.error} onRetry={() => void marks.refetch()} isEmpty={!marks.data?.length}>
        {marks.data ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead className="text-xs uppercase text-[#9ca3af]">
                <tr>
                  <th className="px-2 py-2">Course</th>
                  <th className="px-2 py-2">Marks</th>
                  <th className="px-2 py-2">Grade</th>
                  <th className="px-2 py-2">Published</th>
                </tr>
              </thead>
              <tbody>
                {marks.data.map((m) => (
                  <tr key={`${m.assessment_id}-${m.component_id}`} className="border-t border-[#f1f5f9]">
                    <td className="px-2 py-3">{m.course_code ?? "—"}</td>
                    <td className="px-2 py-3">
                      {m.marks_obtained}/{m.max_marks}
                    </td>
                    <td className="px-2 py-3">{m.grade_letter ?? "—"}</td>
                    <td className="px-2 py-3 text-xs">{formatDateTime(m.published_at)}</td>
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

function SubjectMarksView() {
  const subjects = useCiaSubjectMarks();
  return (
    <SectionPanel title="Subject-wise internal marks">
      <QueryState isLoading={subjects.isLoading} isError={subjects.isError} error={subjects.error} onRetry={() => void subjects.refetch()} isEmpty={!subjects.data?.length}>
        {subjects.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {subjects.data.map((s) => (
              <li key={s.course_code} className="py-3">
                <p className="font-medium">{s.course_code}</p>
                <p className="text-xs text-[#6b7280]">
                  {s.total_obtained}/{s.total_max}
                  {s.weighted_percentage != null ? ` · ${s.weighted_percentage.toFixed(1)}%` : ""}
                </p>
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function CorrectionsView() {
  const corrections = useCiaCorrections(50, 0);
  return (
    <SectionPanel title="Marks corrections">
      <QueryState isLoading={corrections.isLoading} isError={corrections.isError} error={corrections.error} onRetry={() => void corrections.refetch()} isEmpty={!corrections.data?.items.length}>
        {corrections.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {corrections.data.items.map((c) => (
              <li key={c.id} className="py-3">
                <StatusBadge label={c.status} tone={toneForStatus(c.status)} />
                <p className="mt-1 text-[#6b7280]">{c.reason}</p>
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function HistoryView() {
  const history = useCiaHistory(50, 0);
  return (
    <SectionPanel title="CIA history">
      <QueryState isLoading={history.isLoading} isError={history.isError} error={history.error} onRetry={() => void history.refetch()} isEmpty={!history.data?.items.length}>
        {history.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {history.data.items.map((h, i) => (
              <li key={`${h.component_id}-${i}`} className="py-2">
                {h.marks_obtained}/{h.max_marks} · {h.status} · {formatDateTime(h.updated_at)}
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function ComponentsView() {
  const initial = useAssessmentIdFromQuery();
  const [assessmentId, setAssessmentId] = useState(initial);
  const components = useCiaComponents(assessmentId || null);
  return (
    <SectionPanel title="Assessment components">
      <AssessmentIdPicker value={assessmentId} onChange={setAssessmentId} />
      <QueryState isLoading={components.isLoading} isError={components.isError} error={components.error} onRetry={() => void components.refetch()} isEmpty={!components.data?.length}>
        {components.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {components.data.map((c) => (
              <li key={c.component_id} className="py-3">
                <p className="font-medium">
                  {c.code} — {c.name}
                </p>
                <p className="text-xs text-[#6b7280]">
                  Max {c.max_marks} · weight {c.weight_percent}%
                </p>
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}