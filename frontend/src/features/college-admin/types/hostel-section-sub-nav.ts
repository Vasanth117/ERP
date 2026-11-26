export type HostelSectionSubNavItem = {
  key: string;
  label: string;
  href: string;
  icon_key: string;
  active: boolean;
};

export type HostelSectionSubNav = {
  path: string;
  section_key: string | null;
  items: HostelSectionSubNavItem[];
};