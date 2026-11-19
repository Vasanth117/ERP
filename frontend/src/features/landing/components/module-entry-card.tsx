import Image from "next/image";
import Link from "next/link";

import { EntryArrow } from "@/features/landing/components/entry-arrow";
import type { LandingModule } from "@/features/landing/modules";
import { landingModuleHref } from "@/features/landing/modules";
import { cn } from "@/lib/utils";

type ModuleEntryCardProps = {
  module: LandingModule;
};

export function ModuleEntryCard({ module }: ModuleEntryCardProps) {
  const isFeatured = module.variant === "featured";

  return (
    <Link
      href={landingModuleHref(module.id)}
      className={cn(
        "group flex items-center gap-3 rounded-2xl border px-3.5 py-4 shadow-[0px_1px_1px_rgba(23,43,69,0.04),0px_4px_7px_rgba(23,43,69,0.05)] transition-[border-color,box-shadow,background]",
        isFeatured
          ? "col-span-full h-24 w-full border-[#2c4a78] bg-gradient-to-r from-[#172b45] to-[#1f3a64] hover:border-[#3a5f9a] hover:shadow-[0px_2px_6px_rgba(23,43,69,0.06),0px_12px_28px_rgba(36,93,216,0.18)]"
          : "h-28 border-[#e3e9f2] bg-white hover:border-[#245dd8] hover:border-[1.5px] hover:shadow-[0px_2px_6px_rgba(23,43,69,0.06),0px_12px_28px_rgba(36,93,216,0.18)]",
      )}
    >
      <div className="relative flex size-[60px] shrink-0 items-center justify-center">
        <Image
          src={module.icon}
          alt=""
          width={48}
          height={48}
          className="size-12 object-contain"
        />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p
            className={cn(
              "min-w-0 flex-1 text-sm font-semibold leading-snug transition-colors",
              isFeatured
                ? "text-white"
                : "text-[#172b45] group-hover:text-[#245dd8]",
            )}
          >
            {module.title}
          </p>
          <EntryArrow tone={isFeatured ? "featured" : "default"} />
        </div>
        <p
          className={cn(
            "mt-[5px] text-[12.5px] leading-[17px]",
            isFeatured ? "text-[#b9c7dc]" : "text-[#607086]",
          )}
        >
          {module.description}
        </p>
      </div>
    </Link>
  );
}