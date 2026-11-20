import type { LoginPortal } from "@/lib/auth/login-portal";

/**
 * College login shell — change these values (or load from tenant settings later)
 * to match each institution’s template, colors, and hero artwork.
 */
export const loginBranding = {
  productName: "College ERP",
  /**
   * Set to a path under `public/` (e.g. `/login/college-hero.png`) to replace the default art.
   * `null` uses the bundled placeholder illustration below.
   */
  illustrationSrc: null as string | null,
  illustrationAlt: "College campus illustration",
  /** Fallback when `illustrationSrc` is null */
  defaultIllustrationSrc: "/landing/2486e.png",
  colors: {
    pageBackground: "#eef2f6",
    cardBorder: "#e3e9f2",
    panelGradientFrom: "#e8f1ff",
    panelGradientVia: "#f0f6ff",
    panelGradientTo: "#f8fafc",
    headline: "#172b45",
    tagline: "#607086",
    primary: "#245dd8",
    primaryHover: "#1e52c4",
    primarySoft: "#93b4f6",
    logoBackground: "#ffffff",
    logoBorder: "#dbeafe",
    logoIcon: "#245dd8",
  },
} as const;

export function loginLeftPanelCopy(portal: LoginPortal): {
  headline: string;
  tagline: string;
} {
  switch (portal) {
    case "institution":
      return {
        headline: "Welcome back to your campus hub",
        tagline: "Log in to manage academics, staff, and institutional records.",
      };
    case "student-performance":
      return {
        headline: "Welcome back",
        tagline: "Log in to view grades, attendance, and academic progress.",
      };
    default:
      return {
        headline: "Welcome back to College ERP",
        tagline: "Log in to access your modules and campus services.",
      };
  }
}

export function loginFormTitle(portal: LoginPortal): string {
  switch (portal) {
    case "institution":
      return `Sign in to ${loginBranding.productName}`;
    case "student-performance":
      return `Sign in to ${loginBranding.productName}`;
    default:
      return `Sign in to ${loginBranding.productName}`;
  }
}

export function loginFormSubtitle(portal: LoginPortal): string {
  switch (portal) {
    case "institution":
      return "Welcome back — access institution management tools.";
    case "student-performance":
      return "Welcome back — sign in with your student or parent ID.";
    default:
      return "Welcome back — use the credentials provided by your college.";
  }
}