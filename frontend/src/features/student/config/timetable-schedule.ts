export const TIMETABLE_SCHEDULE_PATH = "/student/timetable/schedule";

export type TimetableViewKey = "day" | "week" | "month" | "laboratory";

export const TIMETABLE_VIEW_OPTIONS: { key: TimetableViewKey; label: string; figmaFrame: string }[] = [
  { key: "day", label: "Day", figmaFrame: "164:14590" },
  { key: "week", label: "Week", figmaFrame: "164:15251" },
  { key: "month", label: "Month", figmaFrame: "ST 05" },
  { key: "laboratory", label: "Laboratory", figmaFrame: "164:15884" },
];

export function parseTimetableView(raw: string | null): TimetableViewKey {
  if (raw === "week" || raw === "month" || raw === "laboratory") return raw;
  return "day";
}