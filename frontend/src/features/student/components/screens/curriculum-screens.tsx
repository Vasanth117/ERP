"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";

import {
  DetailRow,
  PageHeading,
  QueryState,
  SectionPanel,
} from "@/features/student/components/ui/student-screen-ui";
import { screenBySlug } from "@/features/student/config/screens";
import {
  CourseCodePicker,
  useCourseCodeFromQuery,
} from "@/features/student/components/screens/course-code-picker";
import {
  useCurriculum,
  useEnrolledCourses,
  useCourseInfo,
  useLearningOutcomes,
  usePrerequisites,
  useSemesterSubjects,
  useSyllabus,
} from "@/features/student/hooks/use-student-curriculum";

type CurriculumSlug =
  | "curriculum"
  | "programme-curriculum"
  | "enrolled-courses"
  | "semester-subjects"
  | "course-syllabus"
  | "learning-outcomes"
  | "course-prerequisites"
  | "course-information";

export function CurriculumScreen({ slug }: { slug: CurriculumSlug }) {
  const def = screenBySlug(slug);
  return (
    <div>
      <PageHeading
        title={def?.title ?? "Curriculum"}
        description={def?.description}
        figmaPage="ST 03"
      />
      <CurriculumBody slug={slug} />
    </div>
  );
}

function CurriculumBody({ slug }: { slug: CurriculumSlug }) {
  switch (slug) {
    case "curriculum":
    case "programme-curriculum":
      return <ProgrammeCurriculumView />;
    case "enrolled-courses":
      return <EnrolledCoursesView />;
    case "semester-subjects":
      return <SemesterSubjectsView />;
    case "course-syllabus":
      return <CourseSyllabusView />;
    case "learning-outcomes":
      return <LearningOutcomesView />;
    case "course-prerequisites":
      return <PrerequisitesView />;
    case "course-information":
      return <CourseInfoView />;
    default:
      return null;
  }
}

function ProgrammeCurriculumView() {
  const curriculum = useCurriculum();
  return (
    <SectionPanel title="Programme curriculum">
      <QueryState
        isLoading={curriculum.isLoading}
        isError={curriculum.isError}
        error={curriculum.error}
        onRetry={() => void curriculum.refetch()}
      >
        {curriculum.data ? (
          <>
            <DetailRow label="Programme" value={curriculum.data.programme_code} />
            <DetailRow
              label="Term"
              value={`${curriculum.data.academic_year_label} · ${curriculum.data.semester_label}`}
            />
            <DetailRow label="Version" value={curriculum.data.version} />
            {curriculum.data.summary ? (
              <p className="mt-4 text-sm text-[#6b7280]">{curriculum.data.summary}</p>
            ) : null}
            {curriculum.data.academic_regulations.length > 0 ? (
              <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-[#4b5563]">
                {curriculum.data.academic_regulations.map((rule) => (
                  <li key={rule}>{rule}</li>
                ))}
              </ul>
            ) : null}
          </>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function EnrolledCoursesView() {
  const courses = useEnrolledCourses();
  return (
    <SectionPanel title="Enrolled courses">
      <QueryState
        isLoading={courses.isLoading}
        isError={courses.isError}
        error={courses.error}
        onRetry={() => void courses.refetch()}
        isEmpty={!courses.data?.length}
        emptyMessage="No enrolled courses for this term."
      >
        {courses.data ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px] text-left text-sm">
              <thead className="text-xs uppercase text-[#9ca3af]">
                <tr>
                  <th className="px-2 py-2">Code</th>
                  <th className="px-2 py-2">Name</th>
                  <th className="px-2 py-2">Section</th>
                  <th className="px-2 py-2">Credits</th>
                </tr>
              </thead>
              <tbody>
                {courses.data.map((c) => (
                  <tr key={c.course_id} className="border-t border-[#f1f5f9]">
                    <td className="px-2 py-3 font-medium">{c.course_code}</td>
                    <td className="px-2 py-3">{c.name}</td>
                    <td className="px-2 py-3">{c.section_code ?? "—"}</td>
                    <td className="px-2 py-3">{c.credit_units}</td>
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

function SemesterSubjectsView() {
  const subjects = useSemesterSubjects();
  return (
    <SectionPanel title="Semester subjects">
      <QueryState
        isLoading={subjects.isLoading}
        isError={subjects.isError}
        error={subjects.error}
        onRetry={() => void subjects.refetch()}
        isEmpty={!subjects.data?.subjects.length}
        emptyMessage="No subjects listed."
      >
        {subjects.data ? (
          <ul className="divide-y divide-[#f1f5f9]">
            {subjects.data.subjects.map((s) => (
              <li key={s.subject_id} className="flex justify-between gap-4 py-3 text-sm">
                <div>
                  <p className="font-medium text-[#111827]">
                    {s.subject_code} · {s.name}
                  </p>
                  {s.description ? (
                    <p className="text-xs text-[#6b7280]">{s.description}</p>
                  ) : null}
                </div>
                <span className="text-xs text-[#9ca3af]">{s.credit_units} cr</span>
              </li>
            ))}
          </ul>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function CourseSyllabusView() {
  const params = useSearchParams();
  const initial = useCourseCodeFromQuery(params);
  const [courseCode, setCourseCode] = useState(initial);
  const syllabus = useSyllabus(courseCode || null);

  return (
    <SectionPanel title="Syllabus">
      <CourseCodePicker value={courseCode} onChange={setCourseCode} />
      <QueryState
        isLoading={syllabus.isLoading}
        isError={syllabus.isError}
        error={syllabus.error}
        onRetry={() => void syllabus.refetch()}
        isEmpty={!courseCode}
        emptyMessage="Select a course."
      >
        {syllabus.data ? (
          <div className="space-y-4">
            {syllabus.data.objectives.length > 0 ? (
              <div>
                <h4 className="text-sm font-semibold text-[#111827]">Objectives</h4>
                <ul className="mt-2 list-disc pl-5 text-sm text-[#4b5563]">
                  {syllabus.data.objectives.map((o) => (
                    <li key={o}>{o}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {syllabus.data.units.map((unit, idx) => (
              <div key={`${unit.title}-${idx}`} className="rounded-lg border border-[#f1f5f9] p-3">
                <p className="font-medium text-[#111827]">{unit.title}</p>
                <ul className="mt-2 list-disc pl-5 text-sm text-[#6b7280]">
                  {unit.topics.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function LearningOutcomesView() {
  const params = useSearchParams();
  const initial = useCourseCodeFromQuery(params);
  const [courseCode, setCourseCode] = useState(initial);
  const outcomes = useLearningOutcomes(courseCode || null);

  return (
    <SectionPanel title="Learning outcomes">
      <CourseCodePicker value={courseCode} onChange={setCourseCode} />
      <QueryState
        isLoading={outcomes.isLoading}
        isError={outcomes.isError}
        error={outcomes.error}
        onRetry={() => void outcomes.refetch()}
        isEmpty={!outcomes.data?.outcomes.length}
        emptyMessage={courseCode ? "No outcomes published." : "Select a course."}
      >
        {outcomes.data ? (
          <ol className="list-decimal space-y-2 pl-5 text-sm text-[#4b5563]">
            {outcomes.data.outcomes.map((o) => (
              <li key={o}>{o}</li>
            ))}
          </ol>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function PrerequisitesView() {
  const params = useSearchParams();
  const initial = useCourseCodeFromQuery(params);
  const [courseCode, setCourseCode] = useState(initial);
  const prereq = usePrerequisites(courseCode || null);

  return (
    <SectionPanel title="Prerequisites">
      <CourseCodePicker value={courseCode} onChange={setCourseCode} />
      <QueryState
        isLoading={prereq.isLoading}
        isError={prereq.isError}
        error={prereq.error}
        onRetry={() => void prereq.refetch()}
        isEmpty={!courseCode}
        emptyMessage="Select a course."
      >
        {prereq.data ? (
          <div className="space-y-3 text-sm">
            <DetailRow
              label="Prerequisite course IDs"
              value={prereq.data.prerequisite_course_ids.join(", ") || "—"}
            />
            <DetailRow
              label="Corequisite course IDs"
              value={prereq.data.corequisite_course_ids.join(", ") || "—"}
            />
            <DetailRow label="Minimum CGPA" value={prereq.data.min_cgpa ?? "—"} />
            {prereq.data.notes ? <p className="text-[#6b7280]">{prereq.data.notes}</p> : null}
          </div>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}

function CourseInfoView() {
  const params = useSearchParams();
  const initial = useCourseCodeFromQuery(params);
  const [courseCode, setCourseCode] = useState(initial);
  const info = useCourseInfo(courseCode || null);

  return (
    <SectionPanel title="Course information">
      <CourseCodePicker value={courseCode} onChange={setCourseCode} />
      <QueryState
        isLoading={info.isLoading}
        isError={info.isError}
        error={info.error}
        onRetry={() => void info.refetch()}
        isEmpty={!courseCode}
        emptyMessage="Select a course."
      >
        {info.data ? (
          <>
            <DetailRow label="Name" value={info.data.name} />
            <DetailRow label="Credits" value={info.data.credit_units} />
            <DetailRow label="Description" value={info.data.description} />
            {info.data.faculty.length > 0 ? (
              <div className="mt-4">
                <h4 className="text-sm font-semibold text-[#111827]">Faculty</h4>
                <ul className="mt-2 divide-y divide-[#f1f5f9]">
                  {info.data.faculty.map((f) => (
                    <li key={f.faculty_user_id} className="py-2 text-sm">
                      {f.display_name} · Section {f.section}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </>
        ) : null}
      </QueryState>
    </SectionPanel>
  );
}