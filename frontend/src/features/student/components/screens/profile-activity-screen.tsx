"use client";

import { StudentPageToolbar, StudentCaPanel } from "@/features/student/components/ui/student-ca-panels";
import { QueryState, formatDateTime } from "@/features/student/components/ui/student-screen-ui";
import { useProfileActivities } from "@/features/student/hooks/use-student-profile";

export function StudentProfileActivityScreen() {
  const activities = useProfileActivities(50, 0);

  return (
    <div className="space-y-5" data-figma-page="ST 01">
      <StudentPageToolbar
        title="Profile activity"
        description="Recent actions on your student account."
      />
      <StudentCaPanel title="Activity log">
        <QueryState
          isLoading={activities.isLoading}
          isError={activities.isError}
          error={activities.error}
          onRetry={() => void activities.refetch()}
          isEmpty={!activities.data?.items.length}
          emptyMessage="No activity recorded yet."
        >
          {activities.data ? (
            <ul className="divide-y divide-[#f1f5f9]">
              {activities.data.items.map((row) => (
                <li key={row.id} className="flex justify-between gap-4 py-3 text-sm">
                  <div>
                    <p className="font-medium text-[#111827]">{row.title}</p>
                    <p className="text-xs capitalize text-[#9ca3af]">
                      {row.activity_type.replace(/_/g, " ")}
                    </p>
                    {row.description ? (
                      <p className="mt-1 text-xs text-[#6b7280]">{row.description}</p>
                    ) : null}
                  </div>
                  <time className="shrink-0 text-xs text-[#9ca3af]">
                    {formatDateTime(row.created_at)}
                  </time>
                </li>
              ))}
            </ul>
          ) : null}
        </QueryState>
      </StudentCaPanel>
    </div>
  );
}