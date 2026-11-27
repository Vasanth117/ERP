export type LmsSectionSubNavItem = {
  key: string;
  label: string;
  href: string;
  icon_key: string;
  active: boolean;
};

export type LmsSectionSubNav = {
  path: string;
  section_key: string | null;
  items: LmsSectionSubNavItem[];
};