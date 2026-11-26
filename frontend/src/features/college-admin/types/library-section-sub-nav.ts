export type LibrarySectionSubNavItem = {
  key: string;
  label: string;
  href: string;
  icon_key: string;
  active: boolean;
};

export type LibrarySectionSubNav = {
  path: string;
  section_key: string | null;
  items: LibrarySectionSubNavItem[];
};