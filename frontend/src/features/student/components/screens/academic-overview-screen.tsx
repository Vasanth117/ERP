"use client";

import { useCallback } from "react";
import { ArrowDownToLineIcon } from "@/components/icons/erp/generated/arrow-down-to-line";
import { CheckIcon } from "@/components/icons/erp/generated/check";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import { useAcademicDetails } from "@/features/student/hooks/use-student-academics";
import type { EnrollmentLine } from "@/features/student/types/academics";
import { cn } from "@/lib/utils";

export function AcademicOverviewScreen() {
  const { data, isLoading, isError, error, refetch } = useAcademicDetails();

  // Dynamic values derived from authoritative backend / database payload
  const currentSemester =
    data?.academic_information?.current_semester_number ??
    (data?.enrollment_status?.semester_label
      ? parseInt(data.enrollment_status.semester_label.replace(/\D/g, "") || "1", 10)
      : 1);
  const totalSemesters =
    (data?.academic_record?.eligibility_summary?.total_semesters as number) || 8;
  const completedSemesters = Math.max(0, currentSemester - 1);

  const creditsEarned = data?.academic_record?.credits_earned ?? 0;
  const totalCredits =
    (data?.academic_record?.eligibility_summary?.minimum_credits_required as number) ||
    160;

  const rawProgramme =
    data?.admission?.programme_name ||
    data?.department_programme?.programme_name ||
    data?.admission?.programme_code ||
    "—";
  const programmeDisplay =
    rawProgramme !== "—" &&
    !rawProgramme.startsWith("B.E.") &&
    !rawProgramme.startsWith("B.Tech") &&
    !rawProgramme.startsWith("M.E.") &&
    !rawProgramme.startsWith("MBA")
      ? `B.E. ${rawProgramme}`
      : rawProgramme;

  const regulationLabel = data?.academic_information?.regulation_label ?? "—";
  const admissionType = data?.academic_information?.admission_type ?? "Regular";
  const enrollmentStatus = data?.enrollment_status?.enrollment_status ?? "ACTIVE";
  const statusDisplay =
    enrollmentStatus.toUpperCase() === "ACTIVE"
      ? "Active"
      : enrollmentStatus.replace(/_/g, " ");

  // Fully dynamic registered subjects from MongoDB backend - zero static/hardcoded fixtures
  const displaySubjects: EnrollmentLine[] = data?.current_enrollments ?? [];
  const totalRegisteredCredits = displaySubjects.reduce(
    (sum, s) => sum + (s.credits ?? 0),
    0
  );

  const handleDownloadSummary = useCallback(() => {
    if (!data) return;
    const summaryPayload = {
      title: "Academic Overview Summary",
      student_id: data.admission.student_id,
      roll_number: data.admission.roll_number,
      programme: programmeDisplay,
      regulation: regulationLabel,
      current_semester: currentSemester,
      total_semesters: totalSemesters,
      credits_earned: creditsEarned,
      total_credits: totalCredits,
      enrollment_status: statusDisplay,
      registered_subjects: displaySubjects,
      generated_at: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(summaryPayload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `academic-overview-${data.admission.roll_number ?? "student"}-sem${currentSemester}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [
    data,
    programmeDisplay,
    regulationLabel,
    currentSemester,
    totalSemesters,
    creditsEarned,
    totalCredits,
    statusDisplay,
    displaySubjects,
  ]);

  const semestersList = Array.from({ length: totalSemesters }, (_, i) => i + 1);

  const creditsPercent =
    totalCredits > 0
      ? Math.min(100, Math.round((creditsEarned / totalCredits) * 100))
      : 0;
  const semestersPercent =
    totalSemesters > 0
      ? Math.min(100, Math.round((completedSemesters / totalSemesters) * 100))
      : 0;

  return (
    <div className="space-y-6" data-figma-page="ST 02" data-figma-frame="164:3628">
      {/* 1. Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-[26px] font-bold tracking-tight text-[#111827]">
            Academic Overview
          </h1>
          <p className="mt-1 text-[14px] text-[#6b7280]">
            Your progress from admission to Semester {currentSemester}
          </p>
        </div>
        <div>
          <button
            type="button"
            onClick={handleDownloadSummary}
            className="inline-flex h-9 items-center gap-2 rounded-lg bg-[#2563eb] px-4 text-xs font-medium text-white shadow-sm transition-colors hover:bg-[#1d4ed8]"
          >
            <ArrowDownToLineIcon className="size-3.5 stroke-[2]" aria-hidden />
            <span>Download summary</span>
          </button>
        </div>
      </div>

      <QueryState
        isLoading={isLoading}
        isError={isError}
        error={error}
        onRetry={() => void refetch()}
      >
        {/* 2. Semester Stepper / Timeline Card */}
        <section
          aria-label="Semester progress timeline"
          className="overflow-x-auto rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]"
        >
          <div className="flex min-w-[720px] items-center justify-between py-1">
            {semestersList.map((sem, idx) => {
              const isCompleted = sem < currentSemester;
              const isCurrent = sem === currentSemester;
              const isLast = idx === semestersList.length - 1;

              return (
                <div key={sem} className="flex flex-1 items-center last:flex-none">
                  {/* Stepper node circle & label */}
                  <div className="flex items-center gap-2">
                    {isCompleted ? (
                      <span
                        className="flex size-6 shrink-0 items-center justify-center rounded-full bg-[#2563eb] text-white shadow-sm"
                        title={`Semester ${sem} Completed`}
                      >
                        <CheckIcon className="size-3.5 stroke-[2.5]" aria-hidden />
                      </span>
                    ) : isCurrent ? (
                      <span
                        className="flex size-6 shrink-0 items-center justify-center rounded-full border-2 border-[#2563eb] bg-white text-[12px] font-bold text-[#2563eb] shadow-sm ring-2 ring-[#dbeafe]"
                        title={`Semester ${sem} In Progress`}
                      >
                        {sem}
                      </span>
                    ) : (
                      <span
                        className="flex size-6 shrink-0 items-center justify-center rounded-full bg-[#f1f5f9] text-[12px] font-medium text-[#9ca3af]"
                        title={`Semester ${sem} Upcoming`}
                      >
                        {sem}
                      </span>
                    )}

                    <span
                      className={cn(
                        "text-[13px] font-medium whitespace-nowrap",
                        isCurrent
                          ? "font-bold text-[#111827]"
                          : isCompleted
                            ? "text-[#111827]"
                            : "text-[#9ca3af]",
                      )}
                    >
                      Sem {sem}
                    </span>
                  </div>

                  {/* Connecting line */}
                  {!isLast ? (
                    <div
                      className={cn(
                        "mx-3 h-[2px] min-w-[1.5rem] flex-1 rounded-full",
                        isCompleted || isCurrent ? "bg-[#2563eb]" : "bg-[#e2e8f0]",
                      )}
                      aria-hidden
                    />
                  ) : null}
                </div>
              );
            })}
          </div>
        </section>

        {/* 3. 4-Column Stat Cards Row */}
        <section aria-label="Academic key metrics" className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Card 1: Programme */}
          <div className="flex min-h-[110px] flex-col justify-between rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <span className="text-[13px] font-medium text-[#6b7280]">Programme</span>
            <div className="mt-2">
              <p className="text-[22px] font-bold tracking-tight text-[#111827]">
                {programmeDisplay}
              </p>
              <p className="mt-1 text-[13px] font-medium text-[#2563eb]">
                {regulationLabel}
              </p>
            </div>
          </div>

          {/* Card 2: Current semester */}
          <div className="flex min-h-[110px] flex-col justify-between rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <span className="text-[13px] font-medium text-[#6b7280]">Current semester</span>
            <div className="mt-2">
              <p className="text-[28px] font-bold leading-none tracking-tight tabular-nums text-[#111827]">
                {currentSemester}
              </p>
              <p className="mt-1.5 text-[13px] font-medium text-[#2563eb]">
                of {totalSemesters}
              </p>
            </div>
          </div>

          {/* Card 3: Credits earned */}
          <div className="flex min-h-[110px] flex-col justify-between rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <span className="text-[13px] font-medium text-[#6b7280]">Credits earned</span>
            <div className="mt-2">
              <p className="text-[28px] font-bold leading-none tracking-tight tabular-nums text-[#111827]">
                {creditsEarned}
              </p>
              <p className="mt-1.5 text-[13px] font-medium text-[#6b7280]">
                of {totalCredits}
              </p>
            </div>
          </div>

          {/* Card 4: Status */}
          <div className="flex min-h-[110px] flex-col justify-between rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <span className="text-[13px] font-medium text-[#6b7280]">Status</span>
            <div className="mt-2">
              <p className="text-[22px] font-bold tracking-tight text-[#111827]">
                {statusDisplay}
              </p>
              <p className="mt-1 text-[13px] font-medium text-[#059669]">
                {admissionType}
              </p>
            </div>
          </div>
        </section>

        {/* 4. Bottom Main Content Grid (Registered Subjects Table & Programme Progress) */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Left: Registered Subjects (No Search Bar, Clean Department Style Table) */}
          <section
            aria-label="Registered subjects"
            className="overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)] lg:col-span-8"
          >
            <div className="border-b border-[#f1f5f9] px-5 py-4">
              <h2 className="text-[15px] font-semibold text-[#111827]">
                Registered subjects
              </h2>
            </div>

            {displaySubjects.length === 0 ? (
              <div className="py-12 text-center">
                <p className="text-sm font-medium text-[#111827]">No registered subjects found</p>
                <p className="mt-1 text-xs text-[#6b7280]">
                  You have no course enrollments registered for this academic term.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[38rem] text-left text-[13px]">
                  <thead>
                    <tr className="border-b border-[#f1f5f9] text-[12px] font-medium text-[#6b7280]">
                      <th className="px-5 py-3 font-medium">Code</th>
                      <th className="py-3 pr-3 font-medium">Subject</th>
                      <th className="py-3 pr-3 font-medium">Category</th>
                      <th className="py-3 pr-3 font-medium">Credits</th>
                      <th className="py-3 pr-3 font-medium">Faculty</th>
                      <th className="py-3 pr-5 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {displaySubjects.map((subject) => (
                      <tr
                        key={subject.course_code}
                        className="transition-colors hover:bg-[#f9fafb]"
                      >
                        <td className="px-5 py-3.5 font-mono font-bold text-[#111827]">
                          {subject.course_code}
                        </td>
                        <td className="py-3.5 pr-3 font-medium text-[#374151]">
                          {subject.course_name}
                        </td>
                        <td className="py-3.5 pr-3 text-[#6b7280]">
                          {subject.category ?? "—"}
                        </td>
                        <td className="py-3.5 pr-3 tabular-nums text-[#374151]">
                          {subject.credits ?? "—"}
                        </td>
                        <td className="py-3.5 pr-3 text-[#4b5563]">
                          {subject.faculty_name ?? "—"}
                        </td>
                        <td className="py-3.5 pr-5">
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-[#ecfdf5] px-2.5 py-0.5 text-[11px] font-medium text-[#047857]">
                            <span className="size-1.5 rounded-full bg-[#10b981]" aria-hidden />
                            {subject.status === "ACTIVE" ? "Enrolled" : subject.status.replace(/_/g, " ")}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="border-t border-[#f1f5f9] px-5 py-3 text-[12px] font-medium text-[#6b7280]">
              {displaySubjects.length} subjects · {totalRegisteredCredits} credits
            </div>
          </section>

          {/* Right: Programme Progress */}
          <section
            aria-label="Programme completion progress"
            className="rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)] lg:col-span-4"
          >
            <h2 className="text-[15px] font-semibold text-[#111827]">
              Programme progress
            </h2>

            <div className="mt-6 space-y-6">
              {/* Progress 1: Credits completed */}
              <div>
                <div className="mb-2 flex items-center justify-between text-[13px]">
                  <span className="font-medium text-[#111827]">Credits completed</span>
                  <span className="tabular-nums text-[#6b7280]">
                    {creditsEarned} / {totalCredits}
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-[#f1f5f9]">
                  <div
                    className="h-full rounded-full bg-[#2563eb] transition-all duration-500"
                    style={{ width: `${creditsPercent}%` }}
                  />
                </div>
              </div>

              {/* Progress 2: Semesters completed */}
              <div>
                <div className="mb-2 flex items-center justify-between text-[13px]">
                  <span className="font-medium text-[#111827]">Semesters completed</span>
                  <span className="tabular-nums text-[#6b7280]">
                    {completedSemesters} / {totalSemesters}
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-[#f1f5f9]">
                  <div
                    className="h-full rounded-full bg-[#2563eb] transition-all duration-500"
                    style={{ width: `${semestersPercent}%` }}
                  />
                </div>
              </div>
            </div>
          </section>
        </div>
      </QueryState>
    </div>
  );
}
