"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { DecorativeImage } from "@/components/ui/decorative-image";
import { underConstructionAssets } from "@/features/under-construction/assets";
import { underConstructionPageGradient } from "@/features/under-construction/constants";

/** Figma 342:214 — card centered in frame; footnote at y≈976 in 1024px height. */
export function UnderConstructionView() {
  const router = useRouter();

  useEffect(() => {
    const html = document.documentElement;
    const body = document.body;
    const prev = {
      htmlOverflow: html.style.overflow,
      bodyOverflow: body.style.overflow,
      htmlWidth: html.style.width,
      htmlHeight: html.style.height,
      bodyWidth: body.style.width,
      bodyHeight: body.style.height,
      bodyMargin: body.style.margin,
      bodyOverscroll: body.style.overscrollBehavior,
    };

    html.classList.add("route-under-construction");
    body.classList.add("route-under-construction");
    html.style.overflow = "hidden";
    body.style.overflow = "hidden";
    html.style.width = "100%";
    html.style.height = "100%";
    body.style.width = "100%";
    body.style.height = "100%";
    body.style.margin = "0";
    body.style.overscrollBehavior = "none";

    return () => {
      html.classList.remove("route-under-construction");
      body.classList.remove("route-under-construction");
      html.style.overflow = prev.htmlOverflow;
      body.style.overflow = prev.bodyOverflow;
      html.style.width = prev.htmlWidth;
      html.style.height = prev.htmlHeight;
      body.style.width = prev.bodyWidth;
      body.style.height = prev.bodyHeight;
      body.style.margin = prev.bodyMargin;
      body.style.overscrollBehavior = prev.bodyOverscroll;
    };
  }, []);

  return (
    <div
      className="relative size-full min-w-0 overflow-hidden"
      style={{ backgroundImage: underConstructionPageGradient }}
      data-figma-page="342:213"
      data-figma-frame="342:214"
    >
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
        <div className="absolute -top-[18%] left-[68%] size-[min(560px,40vw)]">
          <DecorativeImage
            src={underConstructionAssets.glowAmber}
            className="size-full scale-125 object-contain"
          />
        </div>
        <div className="absolute -left-[14%] top-[55%] size-[min(600px,42vw)]">
          <DecorativeImage
            src={underConstructionAssets.glowBlue}
            className="size-full scale-125 object-contain"
          />
        </div>
        <div className="absolute -bottom-[18%] left-[48%] size-[min(420px,32vw)]">
          <DecorativeImage
            src={underConstructionAssets.glowTeal}
            className="size-full scale-125 object-contain"
          />
        </div>
        <div className="absolute left-[60px] top-[60px] hidden h-[140px] w-[220px] md:block">
          <DecorativeImage
            src={underConstructionAssets.dotPattern}
            className="size-full object-cover"
          />
        </div>
      </div>

      <main className="relative z-10 flex size-full items-center justify-center px-4 pb-16">
        <div className="mx-auto w-full max-w-[640px] shrink-0 rounded-[28px] border border-[#e3e9f2] bg-white shadow-[0px_2px_6px_rgba(23,43,69,0.05),0px_24px_60px_-12px_rgba(23,43,69,0.1)]">
          <div className="flex flex-col items-center px-8 py-10 text-center md:px-14 md:py-11">
            <div
              className="flex h-[200px] w-[176px] items-center justify-center rounded-[100px]"
              style={{
                background:
                  "radial-gradient(ellipse 88px 100px at center, rgba(255,244,199,1) 0%, rgba(255,244,199,0) 100%)",
              }}
            >
              <Image
                src={underConstructionAssets.sign}
                alt=""
                width={176}
                height={176}
                className="size-[176px] object-contain"
                priority
              />
            </div>

            <div
              className="mt-4 inline-flex items-center gap-1.5 rounded-full border border-[#f5d77a] bg-[#fff4d6] px-3 py-[5px]"
              role="status"
            >
              <Image
                src={underConstructionAssets.statusDot}
                alt=""
                width={6}
                height={6}
                className="size-1.5"
              />
              <span className="text-xs font-semibold text-[#8a6100]">
                Coming soon
              </span>
            </div>

            <h1 className="mt-3.5 text-[28px] font-bold tracking-[-0.5px] text-[#172b45] md:text-[32px]">
              Page Under Construction
            </h1>

            <p className="mt-2.5 max-w-[526px] text-[15px] leading-[23px] text-[#607086]">
              We’re still building this part of the College ERP. It will be
              available in an upcoming release. Thanks for your patience.
            </p>

            <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
              <button
                type="button"
                onClick={() => router.back()}
                className="inline-flex h-[43px] items-center gap-2 rounded-xl border border-[#dce3ec] bg-white px-5 text-sm font-semibold text-[#172b45] transition-colors hover:bg-[#f8fafc]"
              >
                <Image
                  src={underConstructionAssets.iconBack}
                  alt=""
                  width={16}
                  height={16}
                  className="size-4"
                />
                Go Back
              </button>
              <Link
                href="/"
                className="inline-flex h-[43px] items-center gap-2 rounded-xl bg-[#245dd8] px-5 text-sm font-semibold text-white shadow-[0px_8px_18px_-6px_rgba(36,93,216,0.28)] transition-colors hover:bg-[#1f4fc0]"
              >
                <Image
                  src={underConstructionAssets.iconModules}
                  alt=""
                  width={16}
                  height={16}
                  className="size-4"
                />
                Back to Modules
              </Link>
            </div>
          </div>
        </div>
      </main>

      <p className="pointer-events-none fixed bottom-12 left-1/2 z-20 -translate-x-1/2 text-center text-xs font-medium text-[#8a99ad]">
        College ERP · Main Module Launcher
      </p>
    </div>
  );
}