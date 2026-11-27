export type CommunicationSectionSubNavItem = {
  key: string;
  label: string;
  href: string;
  icon_key: string;
  active: boolean;
};

export type CommunicationSectionSubNav = {
  path: string;
  section_key: string | null;
  items: CommunicationSectionSubNavItem[];
};