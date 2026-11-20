"use client";

import { useEffect, useState, type ComponentType, type SVGProps } from "react";

import type { ErpIconName } from "./names";

export type ErpIconProps = SVGProps<SVGSVGElement> & {
  name: ErpIconName;
};

/**
 * Lazy-loads a single icon by Lucide slug so the full library is not bundled at once.
 * Prefer direct imports from `@/components/icons/erp/generated/<slug>` in hot paths (e.g. nav).
 */
export function ErpIcon({ name, ...props }: ErpIconProps) {
  const [Icon, setIcon] = useState<ComponentType<SVGProps<SVGSVGElement>> | null>(
    null,
  );

  useEffect(() => {
    let active = true;
    setIcon(null);
    void import(`./generated/${name}.tsx`).then((mod) => {
      if (!active) return;
      const comp = Object.values(mod).find(
        (v): v is ComponentType<SVGProps<SVGSVGElement>> => typeof v === "function",
      );
      if (comp) setIcon(() => comp);
    });
    return () => {
      active = false;
    };
  }, [name]);

  if (!Icon) return null;
  return <Icon {...props} />;
}