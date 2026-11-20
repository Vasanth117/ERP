"use client";

import { useEffect, useState } from "react";

import { useEnrolledCourses } from "@/features/student/hooks/use-student-curriculum";

export function useCourseCodeFromQuery(searchParams: URLSearchParams | null): string {
  const fromUrl = searchParams?.get("courseCode") ?? "";
  const enrolled = useEnrolledCourses();
  const [code, setCode] = useState(fromUrl);

  useEffect(() => {
    if (fromUrl) setCode(fromUrl);
    else if (!code && enrolled.data?.[0]?.course_code) {
      setCode(enrolled.data[0].course_code);
    }
  }, [fromUrl, enrolled.data, code]);

  return code;
}

export function CourseCodePicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (code: string) => void;
}) {
  const enrolled = useEnrolledCourses();

  if (enrolled.isLoading) {
    return <p className="text-sm text-[#9ca3af]">Loading courses…</p>;
  }

  const options = enrolled.data ?? [];

  return (
    <label className="mb-4 flex max-w-md flex-col gap-1 text-sm">
      <span className="text-xs font-medium text-[#6b7280]">Course</span>
      <select
        className="h-10 rounded-lg border border-[#dce3ec] bg-white px-3 text-[#111827]"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.length === 0 ? <option value="">No enrolled courses</option> : null}
        {options.map((c) => (
          <option key={c.course_id} value={c.course_code}>
            {c.course_code} — {c.name}
          </option>
        ))}
      </select>
    </label>
  );
}