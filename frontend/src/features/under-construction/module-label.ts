import { landingModules } from "@/features/landing/modules";

export function moduleTitleFromId(moduleId: string | null | undefined): string | null {
  if (!moduleId?.trim()) {
    return null;
  }
  const match = landingModules.find((m) => m.id === moduleId);
  return match?.title ?? null;
}