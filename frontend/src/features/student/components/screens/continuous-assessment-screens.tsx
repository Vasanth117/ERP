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
  AssignmentIdPicker,
  useAssignmentIdFromQuery,
} from "@/features/student/components/screens/assignment-id-picker";
import { EventsList } from "@/features/student/components/screens/shared-tables";
import {
  useAssessmentProgress,
  useAssignmentDetail,
  useAssignmentFeedback,
  useAssignmentMarks,
  useAssignments,
  useQuizResults,
  useQuizSchedules,
  useResubmissionEligibility,
  useSubmissionStatus,
} from "@/features/student/hooks/use-student-continuous-assessment";

export type ContinuousAssessmentSlug =
  | "assessments"
  | "assignments"
  | "assignment-detail"
  | "quiz-schedules"
  | "quiz-results"
  | "assignment-marks"
  | "submission-status"
  | "assignment-feedback"
  | "resubmission-eligibility";

export function ContinuousAssessmentScreen({ slug }: { slug: ContinuousAssessmentSlug }) {
  const def = screenBySlug(slug);
  return (
    <div>
      <PageHeading title={def?.title ?? "Assessments"} description={def?.description} figmaPage="ST 08" />
      <ContinuousBody slug={slug} />
    </div>
  );
}

function ContinuousBody({ slug }: { slug: ContinuousAssessmentSlug }) {
  switch (slug) {
    case "assessments":
      return <AssessmentsHub />;
    case "assignments":
      return <AssignmentsView />;
    case "assignment-detail":
      return <AssignmentDetailView />;
    case "quiz-schedules":
      return <QuizSchedulesView />;
    case "quiz-results":
      return <QuizResultsView />;
    case "assignment-marks":
      return <AssignmentMarksView />;
    case "submission-status":
      return <SubmissionStatusView />;
    case "assignment-feedback":
      return <FeedbackView />;
    case "resubmission-eligibility":
      return <ResubmissionView />;
    default:
      return null;
  }
}

function AssessmentsHub() {
  const progress = useAssessmentProgress();
  const assignments = useAssignments();
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <SectionPanel title="Progress overview">
        <QueryState isLoading={progress.isLoading} isError={progress.isError} error={progress.error} onRetry={() => void progress.refetch()} isEmpty={!progress.data?.length}>
          {progress.data ? (
            <ul className="divide-y divide-[#f1f5f9] text-sm">
              {progress.data.map((p) => (
                <li key={p.assignment_id} className="py-2">
                  <p className="font-medium">{p.title}</p>
                  <p className="text-xs text-[#6b7280]">
                    {p.course_code} · {p.submission_status}
                    {p.marks_awarded != null ? ` · ${p.marks_awarded}` : ""}
                  </p>
                </li>
              ))}
            </ul>
          ) : null}
        </QueryState>
      </SectionPanel>
      <SectionPanel title="Assignments due">
        <QueryState isLoading={assignments.isLoading} isError={assignments.isError} error={assignments.error} onRetry={() => void assignments.refetch()} isEmpty={!assignments.data?.length}>
          {assignments.data ? (
            <EventsList
              items={assignments.data.map((a) => ({
                id: a.id,
                title: a.title,
                description: `${a.course_code} · max ${a.max_marks}`,
                event_at: a.deadline_at,
              }))}
            />
          ) : null}
        </QueryState>
      </SectionPanel>
    </div>
  );
}

function AssignmentsView() {
  const list = useAssignments();
  return (
    <SectionPanel title="Assignments">
      <QueryState isLoading={list.isLoading} isError={list.isError} error={list.error} onRetry={() => void list.refetch()} isEmpty={!list.data?.length}>
        {list.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {list.data.map((a) => (
              <li key={a.id} className="py-3">
                <p className="font-medium">{a.title}</p>
                <p className="text-xs text-[#6b7280]">
                  {a.course_code} · due {formatDateTime(a.deadline_at)}
                </p>
                <p className="mt-1 line-clamp-2 text-xs text-[#9ca3af]">{a.instructions_preview}</p>
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function AssignmentDetailView() {
  const initial = useAssignmentIdFromQuery();
  const [id, setId] = useState(initial);
  const detail = useAssignmentDetail(id || null);
  return (
    <SectionPanel title="Assignment detail">
      <AssignmentIdPicker value={id} onChange={setId} />
      <QueryState isLoading={detail.isLoading} isError={detail.isError} error={detail.error} onRetry={() => void detail.refetch()} isEmpty={!id}>
        {detail.data ? (
          <>
            <DetailRow label="Title" value={detail.data.title} />
            <DetailRow label="Course" value={`${detail.data.course_code} · ${detail.data.section}`} />
            <DetailRow label="Deadline" value={formatDateTime(detail.data.deadline_at)} />
            <DetailRow label="Max marks" value={detail.data.max_marks} />
            <p className="mt-4 whitespace-pre-wrap text-sm text-[#4b5563]">{detail.data.instructions}</p>
          </>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function QuizSchedulesView() {
  const quizzes = useQuizSchedules();
  return (
    <SectionPanel title="Quiz schedules">
      <QueryState isLoading={quizzes.isLoading} isError={quizzes.isError} error={quizzes.error} onRetry={() => void quizzes.refetch()} isEmpty={!quizzes.data?.length}>
        {quizzes.data ? (
          <EventsList
            items={quizzes.data.map((q) => ({
              id: q.id,
              title: q.title,
              description: q.course_code,
              event_at: q.scheduled_at,
            }))}
          />
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function QuizResultsView() {
  const results = useQuizResults();
  return (
    <SectionPanel title="Quiz results">
      <QueryState isLoading={results.isLoading} isError={results.isError} error={results.error} onRetry={() => void results.refetch()} isEmpty={!results.data?.length}>
        {results.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {results.data.map((r) => (
              <li key={r.assignment_id} className="py-2">
                {r.title} · {r.marks_awarded ?? "—"}/{r.max_marks}
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function AssignmentMarksView() {
  const marks = useAssignmentMarks();
  return (
    <SectionPanel title="Assignment marks">
      <QueryState isLoading={marks.isLoading} isError={marks.isError} error={marks.error} onRetry={() => void marks.refetch()} isEmpty={!marks.data?.length}>
        {marks.data ? (
          <ul className="divide-y divide-[#f1f5f9] text-sm">
            {marks.data.map((m) => (
              <li key={m.assignment_id} className="flex justify-between py-2">
                <span>{m.title}</span>
                <span>
                  {m.marks_awarded ?? "—"}/{m.max_marks}
                </span>
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function SubmissionStatusView() {
  const initial = useAssignmentIdFromQuery();
  const [id, setId] = useState(initial);
  const status = useSubmissionStatus(id || null);
  return (
    <SectionPanel title="Submission status">
      <AssignmentIdPicker value={id} onChange={setId} />
      <QueryState isLoading={status.isLoading} isError={status.isError} error={status.error} onRetry={() => void status.refetch()} isEmpty={!id}>
        {status.data ? (
          <>
            <DetailRow label="Status" value={<StatusBadge label={status.data.status} tone={toneForStatus(status.data.status)} />} />
            <DetailRow label="Submitted" value={formatDateTime(status.data.submitted_at)} />
            <DetailRow label="File" value={status.data.file_name} />
            <DetailRow label="Late" value={status.data.late ? "Yes" : "No"} />
            <DetailRow label="Evaluated" value={status.data.evaluated ? "Yes" : "No"} />
          </>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function FeedbackView() {
  const initial = useAssignmentIdFromQuery();
  const [id, setId] = useState(initial);
  const feedback = useAssignmentFeedback(id || null);
  return (
    <SectionPanel title="Instructor feedback">
      <AssignmentIdPicker value={id} onChange={setId} />
      <QueryState isLoading={feedback.isLoading} isError={feedback.isError} error={feedback.error} onRetry={() => void feedback.refetch()} isEmpty={!id}>
        {feedback.data ? (
          <>
            <p className="whitespace-pre-wrap text-sm text-[#4b5563]">{feedback.data.feedback}</p>
            <p className="mt-2 text-xs text-[#9ca3af]">{formatDateTime(feedback.data.created_at)}</p>
          </>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function ResubmissionView() {
  const initial = useAssignmentIdFromQuery();
  const [id, setId] = useState(initial);
  const resub = useResubmissionEligibility(id || null);
  return (
    <SectionPanel title="Resubmission eligibility">
      <AssignmentIdPicker value={id} onChange={setId} />
      <QueryState isLoading={resub.isLoading} isError={resub.isError} error={resub.error} onRetry={() => void resub.refetch()} isEmpty={!id}>
        {resub.data ? (
          <>
            <DetailRow label="Eligible" value={resub.data.eligible ? "Yes" : "No"} />
            <DetailRow label="Attempts" value={`${resub.data.attempts_used} / ${resub.data.max_resubmissions}`} />
            {resub.data.reasons.length > 0 ? (
              <ul className="mt-2 list-disc pl-5 text-sm text-[#4b5563]">
                {resub.data.reasons.map((r) => (
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