import { DecorativeImage } from "@/components/ui/decorative-image";
import { landingAssets } from "@/features/landing/assets";

export function LandingBackground() {
  return (
    <>
      <div
        className="pointer-events-none absolute left-[min(620px,40vw)] top-[min(820px,70vh)] size-[min(420px,50vw)] overflow-hidden"
        aria-hidden
      >
        <DecorativeImage
          src={landingAssets.glowTeal}
          className="size-full object-contain"
        />
      </div>
      <div
        className="pointer-events-none absolute -left-44 top-[min(620px,55vh)] size-[min(560px,60vw)] overflow-hidden"
        aria-hidden
      >
        <DecorativeImage
          src={landingAssets.glowViolet}
          className="size-full object-contain"
        />
      </div>
      <div
        className="pointer-events-none absolute -top-40 right-[-60px] size-[min(520px,55vw)] overflow-hidden"
        aria-hidden
      >
        <DecorativeImage
          src={landingAssets.glowBlue}
          className="size-full object-contain"
        />
      </div>
      <div
        className="pointer-events-none absolute bottom-10 right-8 h-[140px] w-[220px] max-lg:hidden"
        aria-hidden
      >
        <DecorativeImage
          src={landingAssets.dotPattern}
          className="size-full object-cover"
        />
      </div>
    </>
  );
}