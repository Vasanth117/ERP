"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { useCiaSchedules } from "@/features/student/hooks/use-student-cia";

export function useAssessmentIdFromQuery(): string {
  const params = useSearchParams();
  const fromUrl = params?.get("assessmentId") ?? "";
  const list = useCiaSchedules();
  const [id, setId] = useState(fromUrl);

  useEffect(() => {
    if (fromUrl) setId(fromUrl);
    else if (!id && list.data?.[0]?.id) setId(list.data[0].id);
  }, [fromUrl, list.data, id]);

  return id;
}

export function AssessmentIdPicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (id: string) => void;
}) {
  const list = useCiaSchedules();
  if (list.isLoading) return <p className="text-sm text-[#9ca3af]">Loading assessments…</p>;
  const items = list.data ?? [];
  return (
    <label className="mb-4 flex max-w-lg flex-col gap-1 text-sm">
      <span className="text-xs font-medium text-[#6b7280]">CIA assessment</span>
      <select
        className="h-10 rounded-lg border border-[#dce3ec] bg-white px-3"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {items.length === 0 ? <option value="">No schedules</option> : null}
        {items.map((a) => (
          <option key={a.id} value={a.id}>
            {a.course_code} · {a.title}
          </option>
        ))}
      </select>
    </label>
  );
}