import { DecorativeImage } from "@/components/ui/decorative-image";
import { landingAssets } from "@/features/landing/assets";

export function LandingHero() {
  return (
    <header className="relative flex h-[140px] w-full shrink-0 items-center overflow-hidden rounded-3xl bg-gradient-to-r from-[#1b44ae] via-[#245dd8] via-[55%] to-[#4c86f5] px-6 shadow-[0px_14px_32px_-10px_rgba(36,93,216,0.25)] md:px-10">
      <div className="relative z-10 flex max-w-[467px] flex-col gap-2">
        <h1 className="text-[26px] font-bold tracking-[-0.4px] text-white md:text-[30px]">
          Select an Entry Point
        </h1>
        <p className="text-sm text-white/78">
          Choose a module to get started. Each card opens its own workspace.
        </p>
      </div>
      <div
        className="pointer-events-none absolute -left-10 top-[90px] size-[140px] overflow-hidden max-md:hidden"
        aria-hidden
      >
        <DecorativeImage
          src={landingAssets.heroCircleSm}
          className="size-full object-contain"
        />
      </div>
      <div
        className="pointer-events-none absolute -top-[120px] right-[180px] size-[260px] overflow-hidden max-lg:hidden"
        aria-hidden
      >
        <DecorativeImage
          src={landingAssets.heroCircleLg}
          className="size-full object-contain"
        />
      </div>
      <div
        className="pointer-events-none absolute right-6 top-[60px] size-[180px] overflow-hidden max-md:hidden"
        aria-hidden
      >
        <DecorativeImage
          src={landingAssets.heroCircleMd}
          className="size-full object-contain"
        />
      </div>
    </header>
  );
}