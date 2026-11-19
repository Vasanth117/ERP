import registry from "@/features/college-admin/config/college-admin-frames.json";

export type CollegeAdminFrame = {
  figmaNodeId: string;
  name: string;
  module: string;
  screen: string;
  moduleKey: string;
  title: string;
  slug: string;
  route: string;
  apiPath?: string;
  viewType?: string;
  synthetic?: boolean;
};

export const collegeAdminFrames = registry.frames as CollegeAdminFrame[];

export function framesForModule(moduleNum: string): CollegeAdminFrame[] {
  return collegeAdminFrames.filter((f) => f.module === moduleNum);
}

export function frameBySlug(moduleKey: string, slug: string): CollegeAdminFrame | undefined {
  return collegeAdminFrames.find(
    (f) => f.moduleKey === moduleKey && f.slug === slug,
  );
}

export function frameByPath(pathname: string): CollegeAdminFrame | undefined {
  const exact = collegeAdminFrames.find((f) => f.route === pathname);
  if (exact) return exact;
  return collegeAdminFrames.find(
    (f) => pathname.startsWith(f.route) && f.route.includes("["),
  );
}

export function moduleTabFromFrames(moduleNum: string) {
  return framesForModule(moduleNum).map((f) => ({
    label: f.screen === "01" ? "Overview" : f.title.replace(/^.*–\s*/, "").slice(0, 24),
    href: f.route,
    figmaFrame: f.figmaNodeId,
    slug: f.slug,
  }));
}