export type AttendanceSectionSubNavItem = {
  key: string;
  label: string;
  href: string;
  icon_key: string;
  active: boolean;
};

export type AttendanceSectionSubNav = {
  path: string;
  section_key: string | null;
  items: AttendanceSectionSubNavItem[];
};