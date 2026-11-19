import { LandingBackground } from "@/features/landing/components/landing-background";
import { LandingHero } from "@/features/landing/components/landing-hero";
import { ModuleEntryCard } from "@/features/landing/components/module-entry-card";
import { landingModules } from "@/features/landing/modules";

export function LandingPage() {
  const standardModules = landingModules.filter((m) => m.variant !== "featured");
  const featured = landingModules.find((m) => m.variant === "featured");

  return (
    <div
      className="relative min-h-screen overflow-x-hidden px-6 py-8 md:px-12 md:py-10"
      style={{
        backgroundImage:
          "linear-gradient(151.93deg, rgb(245, 248, 255) 14.286%, rgb(237, 242, 251) 85.714%)",
      }}
      data-figma-page="308:390020"
      data-figma-frame="338:279"
    >
      <LandingBackground />
      <div className="relative z-10 mx-auto flex w-full max-w-[1440px] flex-col gap-7">
        <LandingHero />
        <div className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2 xl:grid-cols-4">
          {standardModules.map((module) => (
            <ModuleEntryCard key={module.id} module={module} />
          ))}
          {featured ? <ModuleEntryCard module={featured} /> : null}
        </div>
      </div>
    </div>
  );
}