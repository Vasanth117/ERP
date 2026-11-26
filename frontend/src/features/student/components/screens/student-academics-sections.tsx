"use client";

import Link from "next/link";
import type { Route } from "next";
import { useEffect, useMemo, useState } from "react";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import {
  StAcademicsDetailRow,
  StAcademicsOutcomeBadge,
  StAcademicsPageBlock,
  StAcademicsResultBadge,
  StAcademicsSectionCard,
  StAcademicsToggle,
  StDepartmentContactRow,
  displayOrDash,
} from "@/features/student/components/ui/student-academics-figma-ui";
import {
  useConfirmTermEnrollment,
  useEnrollmentDeclaration,
} from "@/features/student/hooks/use-student-academics";
import type { AcademicDetails, EnrollmentLine, SemesterSubjectsTerm } from "@/features/student/types/academics";
import { cn } from "@/lib/utils";

/** ST 02.03 — Programme and Department Details */
export function ProgrammeDepartmentDetailsSection({ data }: { data: AcademicDetails }) {
  const ctx = data.programme_department_context;
  const programme = ctx?.programme;
  const department = ctx?.department;
  const contacts = ctx?.contacts;

  return (
    <StAcademicsPageBlock
      title="Programme and Department Details"
      description="Where you study"
      figmaNode="164:4368"
    >
      <div className="grid items-start gap-6 lg:grid-cols-12">
        <div className="space-y-5 lg:col-span-8">
          <StAcademicsSectionCard title="Programme">
            <div className="space-y-0 px-5 pb-3 pt-1.5">
              <StAcademicsDetailRow
                fields={[
                  { label: "Programme", value: displayOrDash(programme?.programme_name) },
                  { label: "Duration", value: displayOrDash(programme?.duration_label) },
                ]}
              />
              <StAcademicsDetailRow
                fields={[
                  { label: "Total credits", value: displayOrDash(programme?.total_credits) },
                  { label: "Affiliation", value: displayOrDash(programme?.affiliation_name) },
                ]}
              />
              <StAcademicsDetailRow
                fields={[
                  { label: "Accreditation", value: displayOrDash(programme?.accreditation_label) },
                ]}
              />
            </div>
          </StAcademicsSectionCard>

          <StAcademicsSectionCard title="Department">
            <div className="space-y-0 px-5 pb-3 pt-1.5">
              <StAcademicsDetailRow
                fields={[
                  { label: "Department", value: displayOrDash(department?.department_name) },
                  { label: "Head of department", value: displayOrDash(department?.head_of_department_name) },
                ]}
              />
              <StAcademicsDetailRow
                fields={[
                  { label: "Class advisor", value: displayOrDash(department?.class_advisor_name) },
                  { label: "Department email", value: displayOrDash(department?.department_email) },
                ]}
              />
            </div>
          </StAcademicsSectionCard>
        </div>

        <div className="lg:col-span-4">
          <StAcademicsSectionCard title="Department contacts">
            <StDepartmentContactRow
              icon="map-pin"
              label="Office"
              value={displayOrDash(contacts?.office_location)}
            />
            <StDepartmentContactRow
              icon="phone"
              label="Phone"
              value={displayOrDash(contacts?.contact_phone)}
            />
          </StAcademicsSectionCard>
        </div>
      </div>
    </StAcademicsPageBlock>
  );
}

function StAcademicsKpiCard({
  label,
  value,
  hint,
  hintClassName,
}: {
  label: string;
  value: string;
  hint?: string;
  hintClassName?: string;
}) {
  return (
    <div className="flex min-h-[100px] flex-col gap-2 rounded-lg border border-[#dce3ec] bg-white p-5">
      <span className="text-[12px] text-[#607086]">{label}</span>
      <span className="text-[26px] font-semibold leading-none text-[#172b45]">{value}</span>
      {hint ? (
        <span className={`text-[11px] ${hintClassName ?? "text-[#245dd8]"}`}>{hint}</span>
      ) : (
        <span className="text-[11px] text-transparent select-none">—</span>
      )}
    </div>
  );
}

/** ST 02.04 — Current Semester Overview */
export function CurrentSemesterOverviewSection({ data }: { data: AcademicDetails }) {
  const overview = data.current_semester_overview;
  const subjects = data.current_enrollments ?? [];
  const totalCredits = overview?.credits_registered ?? subjects.reduce((s, l) => s + (l.credits ?? 0), 0);

  return (
    <StAcademicsPageBlock
      title="Current Semester Overview"
      description={displayOrDash(overview?.term_subtitle)}
      figmaNode="164:4676"
      actions={
        <Link
          href="/student/timetable"
          className="inline-flex items-center gap-2 rounded-md bg-[#245dd8] px-3.5 py-2 text-[12px] font-semibold text-white hover:bg-[#1d4ed8]"
        >
          <CollegeAdminIcon name="calendar" size={15} className="text-white" />
          Timetable
        </Link>
      }
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StAcademicsKpiCard
          label="Subjects"
          value={String(overview?.subject_count ?? subjects.length)}
          hint={`${totalCredits} credits`}
        />
        <StAcademicsKpiCard
          label="Internal tests"
          value={displayOrDash(overview?.internal_tests_label)}
        />
        <StAcademicsKpiCard
          label="Attendance"
          value={
            overview?.attendance_percent != null ? `${overview.attendance_percent}%` : "—"
          }
          hintClassName="text-[#1f7a45]"
        />
        <StAcademicsKpiCard
          label="Next exam"
          value={displayOrDash(overview?.next_exam_title)}
          hint={overview?.next_exam_date_label ?? undefined}
          hintClassName="text-[#946009]"
        />
      </div>

      <RegisteredSubjectsTable subjects={subjects} className="mt-5" />
    </StAcademicsPageBlock>
  );
}

export function RegisteredSubjectsTable({
  subjects,
  className,
}: {
  subjects: EnrollmentLine[];
  className?: string;
}) {
  const totalCredits = subjects.reduce((sum, s) => sum + (s.credits ?? 0), 0);

  return (
    <StAcademicsSectionCard
      title="Registered subjects"
      footer={
        subjects.length ? `${subjects.length} subjects · ${totalCredits} credits` : undefined
      }
      className={className}
    >
      {subjects.length === 0 ? (
        <p className="px-5 py-10 text-center text-[13px] text-[#607086]">No subjects registered for this term.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[44rem] text-left text-[12px]">
            <thead>
              <tr className="bg-[#f7f9fc] text-[11px] font-medium text-[#607086]">
                <th className="px-5 py-2.5">Code</th>
                <th className="py-2.5 pr-3">Subject</th>
                <th className="py-2.5 pr-3">Category</th>
                <th className="py-2.5 pr-3">Credits</th>
                <th className="py-2.5 pr-3">Faculty</th>
                <th className="px-5 py-2.5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#dce3ec]">
              {subjects.map((subject) => (
                <tr key={subject.course_code} className="text-[#172b45]">
                  <td className="px-5 py-3 font-mono font-medium">{subject.course_code}</td>
                  <td className="py-3 pr-3 font-medium">{subject.course_name}</td>
                  <td className="py-3 pr-3 text-[#607086]">{displayOrDash(subject.category)}</td>
                  <td className="py-3 pr-3 tabular-nums text-[#607086]">
                    {subject.credits ?? "—"}
                  </td>
                  <td className="py-3 pr-3 text-[#607086]">{displayOrDash(subject.faculty_name)}</td>
                  <td className="px-5 py-3">
                    <StAcademicsResultBadge
                      label={subject.status === "ACTIVE" ? "Enrolled" : subject.status.replace(/_/g, " ")}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </StAcademicsSectionCard>
  );
}

/** ST 02.05 — Semester-wise Academic History */
export function SemesterAcademicHistorySection({ data }: { data: AcademicDetails }) {
  const rows = data.semester_academic_history ?? [];

  return (
    <StAcademicsPageBlock
      title="Semester-wise Academic History"
      description="Completed semesters"
      figmaNode="164:5053"
    >
      <StAcademicsSectionCard
        title="Semester history"
        footer={rows.length ? `${rows.length} semesters completed` : undefined}
      >
        {rows.length === 0 ? (
          <p className="px-5 py-10 text-center text-[13px] text-[#607086]">
            No completed semesters recorded yet.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[40rem] text-left text-[12px]">
              <thead>
                <tr className="bg-[#f7f9fc] text-[11px] font-medium text-[#607086]">
                  <th className="px-5 py-2.5">Semester</th>
                  <th className="py-2.5 pr-3">Period</th>
                  <th className="py-2.5 pr-3">Credits earned</th>
                  <th className="py-2.5 pr-3">GPA</th>
                  <th className="px-5 py-2.5">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#dce3ec]">
                {rows.map((row) => (
                  <tr key={row.id} className="text-[#172b45]">
                    <td className="px-5 py-3 font-medium">{row.semester_label}</td>
                    <td className="py-3 pr-3 text-[#607086]">{displayOrDash(row.period_label)}</td>
                    <td className="py-3 pr-3 tabular-nums text-[#607086]">
                      {row.credits_required != null
                        ? `${row.credits_earned} / ${row.credits_required}`
                        : String(row.credits_earned)}
                    </td>
                    <td className="py-3 pr-3 tabular-nums text-[#607086]">
                      {row.gpa != null ? row.gpa.toFixed(2) : "—"}
                    </td>
                    <td className="px-5 py-3">
                      <StAcademicsResultBadge label={row.result_label} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </StAcademicsSectionCard>
    </StAcademicsPageBlock>
  );
}

/** ST 02.08 — Academic Progression Details */
export function AcademicProgressionDetailsSection({ data }: { data: AcademicDetails }) {
  const progression = data.academic_progression;
  const rows = progression?.transitions ?? [];
  const policy = progression?.policy;

  return (
    <StAcademicsPageBlock
      title="Academic Progression Details"
      description="Promotion rules and your status"
      figmaNode="164:6079"
    >
      <div className="grid items-start gap-6 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <StAcademicsSectionCard
            title="Progression"
            footer={rows.length ? `${rows.length} transitions` : undefined}
          >
            {rows.length === 0 ? (
              <p className="px-5 py-10 text-center text-[13px] text-[#607086]">
                No progression transitions recorded yet.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[36rem] text-left text-[12px]">
                  <thead>
                    <tr className="bg-[#f7f9fc] text-[11px] font-medium text-[#607086]">
                      <th className="px-5 py-2.5">Semester</th>
                      <th className="py-2.5 pr-3">Credits earned</th>
                      <th className="py-2.5 pr-3">Required to progress</th>
                      <th className="px-5 py-2.5">Outcome</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#dce3ec]">
                    {rows.map((row, idx) => (
                      <tr key={`${row.transition_label}-${idx}`}>
                        <td className="px-5 py-3 font-medium text-[#172b45]">{row.transition_label}</td>
                        <td className="py-3 pr-3 text-[#607086]">{row.credits_display}</td>
                        <td className="py-3 pr-3 text-[#607086]">{row.requirement_label}</td>
                        <td className="px-5 py-3">
                          <StAcademicsOutcomeBadge label={row.outcome} tone={row.outcome_tone} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </StAcademicsSectionCard>
        </div>

        <div className="lg:col-span-4">
          <StAcademicsSectionCard title="Policy">
            <div className="divide-y divide-[#dce3ec]">
              <div className="flex gap-3 px-5 py-4">
                <CollegeAdminIcon name="calendar" size={18} className="mt-0.5 text-[#607086]" />
                <div>
                  <p className="text-[13px] font-medium text-[#172b45]">Minimum attendance</p>
                  <p className="mt-0.5 text-[12px] text-[#607086]">
                    {policy?.minimum_attendance_percent != null
                      ? `${policy.minimum_attendance_percent}%`
                      : "—"}
                  </p>
                </div>
              </div>
              <div className="flex gap-3 px-5 py-4">
                <CollegeAdminIcon name="info" size={18} className="mt-0.5 text-[#607086]" />
                <div>
                  <p className="text-[13px] font-medium text-[#172b45]">Maximum arrears carried</p>
                  <p className="mt-0.5 text-[12px] text-[#607086]">
                    {displayOrDash(policy?.arrears_rule_label)}
                  </p>
                </div>
              </div>
            </div>
          </StAcademicsSectionCard>
        </div>
      </div>
    </StAcademicsPageBlock>
  );
}

function formatCreditValue(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

/** ST 02.07 — Course Credit Summary */
export function CourseCreditSummarySection({ data }: { data: AcademicDetails }) {
  const summary = data.course_credit_summary;

  if (!summary) {
    return (
      <StAcademicsPageBlock
        title="Course Credit Summary"
        description="Credits by category"
        figmaNode="164:5744"
      >
        <p className="text-[13px] text-[#607086]">Credit summary is not available for your record yet.</p>
      </StAcademicsPageBlock>
    );
  }

  const categories = summary.categories ?? [];

  return (
    <StAcademicsPageBlock
      title="Course Credit Summary"
      description="Credits by category"
      figmaNode="164:5744"
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StAcademicsKpiCard label="Earned" value={formatCreditValue(summary.credits_earned)} />
        <StAcademicsKpiCard
          label="In progress"
          value={formatCreditValue(summary.credits_in_progress)}
          hint={summary.in_progress_semester_label ?? undefined}
        />
        <StAcademicsKpiCard
          label="Remaining"
          value={formatCreditValue(summary.credits_remaining)}
          hintClassName="text-[#607086]"
        />
        <StAcademicsKpiCard
          label="Required"
          value={formatCreditValue(summary.credits_required)}
          hintClassName="text-[#607086]"
        />
      </div>

      <StAcademicsSectionCard
        title="By category"
        footer={categories.length ? `${categories.length} categories` : undefined}
        className="mt-5"
      >
        {categories.length === 0 ? (
          <p className="px-5 py-10 text-center text-[13px] text-[#607086]">
            Category breakdown has not been published for your programme yet.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[32rem] text-left text-[12px]">
              <thead>
                <tr className="bg-[#f7f9fc] text-[11px] font-medium text-[#607086]">
                  <th className="px-5 py-2.5">Category</th>
                  <th className="py-2.5 pr-3">Required</th>
                  <th className="py-2.5 pr-3">Earned</th>
                  <th className="py-2.5 pr-3">In progress</th>
                  <th className="px-5 py-2.5">Remaining</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#dce3ec]">
                {categories.map((row) => (
                  <tr key={row.category} className="text-[#172b45]">
                    <td className="px-5 py-3 font-medium">{row.category}</td>
                    <td className="py-3 pr-3 tabular-nums text-[#607086]">
                      {formatCreditValue(row.credits_required)}
                    </td>
                    <td className="py-3 pr-3 tabular-nums text-[#607086]">
                      {formatCreditValue(row.credits_earned)}
                    </td>
                    <td className="py-3 pr-3 tabular-nums text-[#607086]">
                      {formatCreditValue(row.credits_in_progress)}
                    </td>
                    <td className="px-5 py-3 tabular-nums text-[#607086]">
                      {formatCreditValue(row.credits_remaining)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </StAcademicsSectionCard>
    </StAcademicsPageBlock>
  );
}

function semesterTermKey(term: SemesterSubjectsTerm): string {
  return `${term.academic_year_label}::${term.semester_label}`;
}

function semesterTermLabel(term: SemesterSubjectsTerm): string {
  if (term.semester_number != null) {
    return `Semester ${term.semester_number}`;
  }
  return term.semester_label;
}

function downloadSemesterSubjects(term: SemesterSubjectsTerm) {
  const payload = {
    academic_year_label: term.academic_year_label,
    semester_label: term.semester_label,
    semester_number: term.semester_number,
    subjects: term.subjects,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `semester-subjects-${term.semester_number ?? term.semester_label}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

/** ST 02.06 — Semester Subject List */
export function SemesterSubjectListSection({ data }: { data: AcademicDetails }) {
  const terms = data.semester_subject_terms ?? [];
  const defaultIndex = useMemo(() => {
    const idx = terms.findIndex((t) => t.is_current);
    return idx >= 0 ? idx : 0;
  }, [terms]);
  const [selectedIndex, setSelectedIndex] = useState(defaultIndex);

  useEffect(() => {
    setSelectedIndex(defaultIndex);
  }, [defaultIndex]);

  const resolvedIndex = terms.length ? Math.min(selectedIndex, terms.length - 1) : 0;
  const selected = terms[resolvedIndex];

  return (
    <StAcademicsPageBlock
      title="Semester Subject List"
      description="Choose a semester to view its subjects"
      figmaNode="164:5373"
      actions={
        selected ? (
          <button
            type="button"
            onClick={() => downloadSemesterSubjects(selected)}
            className="inline-flex items-center gap-2 rounded-md bg-[#245dd8] px-3.5 py-2 text-[12px] font-semibold text-white hover:bg-[#1d4ed8]"
          >
            <CollegeAdminIcon name="download" size={15} className="text-white" />
            Download
          </button>
        ) : undefined
      }
    >
      {terms.length === 0 ? (
        <p className="text-[13px] text-[#607086]">No semester registrations found.</p>
      ) : (
        <>
          <div className="mb-5 flex flex-wrap items-center gap-2">
            <label className="inline-flex items-center gap-2 rounded-md border border-[#dce3ec] bg-white px-3.5 py-2 text-[12px] font-semibold text-[#172b45]">
              <CollegeAdminIcon name="calendar" size={15} className="text-[#607086]" />
              <select
                className="cursor-pointer border-0 bg-transparent text-[12px] font-semibold text-[#172b45] outline-none"
                value={resolvedIndex}
                onChange={(e) => setSelectedIndex(Number(e.target.value))}
                aria-label="Select semester"
              >
                {terms.map((term, index) => (
                  <option key={semesterTermKey(term)} value={index}>
                    {semesterTermLabel(term)}
                  </option>
                ))}
              </select>
            </label>
            {selected?.is_current ? (
              <span className="inline-flex items-center gap-1.5 rounded bg-[#ebf2ff] px-2 py-1 text-[11px] font-semibold text-[#245dd8]">
                <span className="size-1.5 rounded-full bg-[#245dd8]" aria-hidden />
                {semesterTermLabel(selected)}
              </span>
            ) : null}
            <span className="ml-auto text-[11px] text-[#607086]">
              AY {selected?.academic_year_label} · {selected?.semester_label}
            </span>
          </div>
          {selected ? <RegisteredSubjectsTable subjects={selected.subjects} /> : null}
        </>
      )}
    </StAcademicsPageBlock>
  );
}

/** ST 02.09 — Enrollment Confirmation */
export function EnrollmentConfirmationSection({ data }: { data: AcademicDetails }) {
  const confirmation = data.enrollment_confirmation;
  const declaration = useEnrollmentDeclaration();
  const confirmEnrollment = useConfirmTermEnrollment();

  if (!confirmation) {
    return (
      <StAcademicsPageBlock
        title="Enrollment Confirmation"
        description="Semester enrollment confirmation"
        figmaNode="164:6396"
      >
        <p className="text-[13px] text-[#607086]">No enrollment confirmation is configured for your record.</p>
      </StAcademicsPageBlock>
    );
  }

  const description =
    confirmation.page_subtitle ??
    (confirmation.target_semester_number != null
      ? `Confirm your Semester ${confirmation.target_semester_number} enrollment when the window opens`
      : "Confirm your next semester enrollment when the window opens");

  const confirming = confirmEnrollment.isPending || declaration.isPending;
  const showActions = !confirmation.already_confirmed;
  const showBanner =
    Boolean(confirmation.window_banner_title?.trim()) ||
    Boolean(confirmation.window_banner_body?.trim());

  return (
    <StAcademicsPageBlock
      title="Enrollment Confirmation"
      description={description}
      figmaNode="164:6396"
      actions={
        showActions ? (
          <div className="flex flex-col items-end gap-1.5">
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={confirming || !confirmation.declaration_accepted}
                onClick={() => declaration.mutate(false)}
                className="inline-flex items-center gap-2 rounded-md border border-[#dce3ec] bg-white px-3.5 py-2 text-[12px] font-semibold text-[#172b45] hover:bg-[#f7f9fc] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <CollegeAdminIcon name="x" size={15} className="text-[#607086]" />
                Cancel
              </button>
              <button
                type="button"
                disabled={!confirmation.can_confirm || confirming}
                onClick={() => confirmEnrollment.mutate()}
                className="inline-flex items-center gap-2 rounded-md bg-[#245dd8] px-3.5 py-2 text-[12px] font-semibold text-white hover:bg-[#1d4ed8] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <CollegeAdminIcon name="check" size={15} className="text-white" />
                Confirm enrollment
              </button>
            </div>
            {confirmEnrollment.isError ? (
              <p className="max-w-xs text-right text-[11px] text-[#c2410c]">
                Confirmation could not be completed. Check eligibility, fees, and the enrollment window.
              </p>
            ) : null}
          </div>
        ) : (
          <StAcademicsOutcomeBadge label="Confirmed" tone="success" />
        )
      }
    >
      {showBanner ? (
        <div className="flex w-full items-center gap-3 rounded-md bg-[#ebf2ff] px-4 py-4">
          <CollegeAdminIcon name="info" size={18} className="shrink-0 text-[#245dd8]" />
          <div className="min-w-0 flex-1">
            {confirmation.window_banner_title ? (
              <p className="text-[12px] font-semibold text-[#172b45]">{confirmation.window_banner_title}</p>
            ) : null}
            {confirmation.window_banner_body ? (
              <p className={cn("text-[11px] text-[#607086]", confirmation.window_banner_title && "mt-1")}>
                {confirmation.window_banner_body}
              </p>
            ) : null}
          </div>
        </div>
      ) : null}

      <div className="mt-5 grid items-start gap-6 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <StAcademicsSectionCard title="Confirmation">
            <div className="px-5 pb-3 pt-1">
              <StAcademicsDetailRow
                fields={[
                  {
                    label: "Semester",
                    value:
                      confirmation.target_semester_number != null
                        ? String(confirmation.target_semester_number)
                        : displayOrDash(confirmation.target_semester_label),
                  },
                  { label: "Eligibility", value: displayOrDash(confirmation.eligibility_label) },
                ]}
              />
              <StAcademicsDetailRow
                fields={[
                  { label: "Fee clearance", value: displayOrDash(confirmation.fee_clearance_label) },
                  { label: "Attendance condition", value: displayOrDash(confirmation.attendance_condition_label) },
                ]}
              />
            </div>
          </StAcademicsSectionCard>
        </div>

        <div className="lg:col-span-4">
          <StAcademicsSectionCard title="Declaration">
            <div className="flex items-center justify-between gap-3 px-5 py-3">
              <span className="text-[13px] font-medium text-[#172b45]">I confirm the details above</span>
              <StAcademicsToggle
                ariaLabel="I confirm the details above"
                checked={confirmation.declaration_accepted}
                disabled={declaration.isPending || confirmation.already_confirmed}
                onChange={(next) => declaration.mutate(next)}
              />
            </div>
          </StAcademicsSectionCard>
          {confirmation.declaration_accepted && !confirmation.can_confirm && !confirmation.already_confirmed ? (
            <ul className="mt-2 space-y-0.5 text-[11px] text-[#607086]">
              {(confirmation.confirm_blocked_reasons ?? []).map((reason) => (
                <li key={reason}>• {reason}</li>
              ))}
            </ul>
          ) : null}
        </div>
      </div>
    </StAcademicsPageBlock>
  );
}

const PENDING_ICON_STYLES: Record<string, string> = {
  alert: "text-[#c2410c]",
  info: "text-[#245dd8]",
};

/** ST 02.11 — Academic Status Details */
export function AcademicStatusDetailsSection({ data }: { data: AcademicDetails }) {
  const status = data.academic_status_details;
  const standing = status?.standing_fields ?? [];
  const requirements = status?.pending_requirements ?? [];
  const description = status?.page_subtitle ?? "Standing, holds and requirements";

  const standingRows: { label: string; value: string }[][] = [];
  for (let i = 0; i < standing.length; i += 2) {
    standingRows.push(standing.slice(i, i + 2).map((f) => ({ label: f.label, value: f.value })));
  }

  return (
    <StAcademicsPageBlock
      title="Academic Status Details"
      description={description}
      figmaNode="164:6990"
    >
      <div className="grid items-start gap-6 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <StAcademicsSectionCard title="Academic standing">
            <div className="space-y-0 px-5 pb-3 pt-1.5">
              {standingRows.length === 0 ? (
                <p className="py-6 text-[13px] text-[#607086]">No standing details are available yet.</p>
              ) : (
                standingRows.map((fields, index) => (
                  <StAcademicsDetailRow key={fields.map((f) => f.label).join("-") || String(index)} fields={fields} />
                ))
              )}
            </div>
          </StAcademicsSectionCard>
        </div>

        <div className="lg:col-span-4">
          <StAcademicsSectionCard title="Pending requirements">
            {requirements.length === 0 ? (
              <p className="px-5 py-10 text-center text-[13px] text-[#607086]">No requirements listed.</p>
            ) : (
              <ul className="divide-y divide-[#dce3ec]">
                {requirements.map((row) => {
                  const iconClass = PENDING_ICON_STYLES[row.icon_tone] ?? PENDING_ICON_STYLES.info!;
                  return (
                    <li key={`${row.title}-${row.status_label}`} className="flex gap-3 px-5 py-4">
                      <CollegeAdminIcon name="info" size={18} className={cn("mt-0.5 shrink-0", iconClass)} />
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <p className="text-[13px] font-medium text-[#172b45]">{row.title}</p>
                          {row.action_href ? (
                            <Link
                              href={row.action_href as Route}
                              className={cn(
                                "inline-flex shrink-0 items-center gap-1.5 rounded px-1.5 py-0.5 text-[11px] font-semibold",
                                row.status_tone === "warning"
                                  ? "bg-[#fff7ed] text-[#c2410c]"
                                  : "border border-[#245dd8] bg-white text-[#245dd8]",
                              )}
                            >
                              <span
                                className={cn(
                                  "size-[5px] rounded-full",
                                  row.status_tone === "warning" ? "bg-[#c2410c]" : "bg-[#245dd8]",
                                )}
                                aria-hidden
                              />
                              {row.status_label}
                            </Link>
                          ) : (
                            <StAcademicsOutcomeBadge label={row.status_label} tone={row.status_tone} />
                          )}
                        </div>
                        {row.detail ? (
                          <p className="mt-1 text-[12px] text-[#607086]">{row.detail}</p>
                        ) : null}
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </StAcademicsSectionCard>
        </div>
      </div>
    </StAcademicsPageBlock>
  );
}

/** ST 02.10 — Enrollment History (term confirmations) */
export function TermEnrollmentHistorySection({ data }: { data: AcademicDetails }) {
  const rows = data.enrollment_confirmation_history ?? [];

  return (
    <StAcademicsPageBlock
      title="Enrollment History"
      description="Past confirmations"
      figmaNode="164:6688"
    >
      <StAcademicsSectionCard
        title="Enrollments"
        footer={rows.length ? `${rows.length} records` : undefined}
      >
        {rows.length === 0 ? (
          <p className="px-5 py-10 text-center text-[13px] text-[#607086]">
            No enrollment confirmations recorded yet.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[36rem] text-left text-[12px]">
              <thead>
                <tr className="bg-[#f7f9fc] text-[11px] font-medium text-[#607086]">
                  <th className="px-5 py-2.5">AY</th>
                  <th className="py-2.5 pr-3">Semester</th>
                  <th className="py-2.5 pr-3">Confirmed on</th>
                  <th className="py-2.5 pr-3">Mode</th>
                  <th className="px-5 py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#dce3ec]">
                {rows.map((row) => (
                  <tr key={row.id} className="text-[#172b45]">
                    <td className="px-5 py-3 font-medium">{row.academic_year_label}</td>
                    <td className="py-3 pr-3 text-[#607086]">
                      {row.semester_number != null ? `Semester ${row.semester_number}` : row.semester_label}
                    </td>
                    <td className="py-3 pr-3 text-[#607086]">{displayOrDash(row.confirmed_on_label)}</td>
                    <td className="py-3 pr-3 text-[#607086]">{displayOrDash(row.study_mode)}</td>
                    <td className="px-5 py-3">
                      <StAcademicsOutcomeBadge label={row.status} tone={row.status_tone} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </StAcademicsSectionCard>
    </StAcademicsPageBlock>
  );
}