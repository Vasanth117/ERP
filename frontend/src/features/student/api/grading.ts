import { apiRequest } from "@/lib/api/client";

export type CgpaRead = {
  cgpa: number | null;
  credits_earned: number;
  credits_required: number | null;
  credits_pending: number | null;
  grading_policy_version: string | null;
};

export async function fetchCgpa(): Promise<CgpaRead> {
  return apiRequest<CgpaRead>("/students/me/grades/gpa/cumulative");
}