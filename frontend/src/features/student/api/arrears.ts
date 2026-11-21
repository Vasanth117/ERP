import { apiRequest } from "@/lib/api/client";

export type BacklogSummaryRead = {
  pending_count: number;
  cleared_count: number;
  registered_count: number;
};

export async function fetchBacklogSummary(): Promise<BacklogSummaryRead> {
  return apiRequest<BacklogSummaryRead>("/students/me/arrears/backlog-summary");
}