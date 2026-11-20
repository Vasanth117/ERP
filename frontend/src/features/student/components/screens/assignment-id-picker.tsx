"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { useAssignments } from "@/features/student/hooks/use-student-continuous-assessment";

export function useAssignmentIdFromQuery(): string {
  const params = useSearchParams();
  const fromUrl = params?.get("assignmentId") ?? "";
  const list = useAssignments();
  const [id, setId] = useState(fromUrl);

  useEffect(() => {
    if (fromUrl) setId(fromUrl);
    else if (!id && list.data?.[0]?.id) setId(list.data[0].id);
  }, [fromUrl, list.data, id]);

  return id;
}

export function AssignmentIdPicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (id: string) => void;
}) {
  const list = useAssignments();
  if (list.isLoading) return <p className="text-sm text-[#9ca3af]">Loading assignments…</p>;
  const items = list.data ?? [];
  return (
    <label className="mb-4 flex max-w-lg flex-col gap-1 text-sm">
      <span className="text-xs font-medium text-[#6b7280]">Assignment</span>
      <select
        className="h-10 rounded-lg border border-[#dce3ec] bg-white px-3"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {items.length === 0 ? <option value="">No assignments</option> : null}
        {items.map((a) => (
          <option key={a.id} value={a.id}>
            {a.course_code} · {a.title}
          </option>
        ))}
      </select>
    </label>
  );
}