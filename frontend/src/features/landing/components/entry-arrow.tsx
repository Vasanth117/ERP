import Image from "next/image";

import { landingAssets } from "@/features/landing/assets";

type EntryArrowProps = {
  tone?: "default" | "featured";
};

/** Figma Module Entry — circular arrow control (default + hover). */
export function EntryArrow({ tone = "default" }: EntryArrowProps) {
  if (tone === "featured") {
    return (
      <span className="inline-flex size-5 shrink-0 items-center justify-center">
        <Image
          src={landingAssets.arrowHover}
          alt=""
          width={20}
          height={20}
          className="size-5"
        />
      </span>
    );
  }

  return (
    <span className="relative inline-flex size-5 shrink-0 items-center justify-center">
      <Image
        src={landingAssets.arrow}
        alt=""
        width={20}
        height={20}
        className="size-5 transition-opacity group-hover:opacity-0"
      />
      <Image
        src={landingAssets.arrowHover}
        alt=""
        width={20}
        height={20}
        className="absolute size-5 opacity-0 transition-opacity group-hover:opacity-100"
      />
    </span>
  );
}