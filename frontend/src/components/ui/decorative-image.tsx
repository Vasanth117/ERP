/**
 * Non-LCP decorative artwork (glows, patterns, hero circles).
 * Uses a native img with low fetch priority so Next/Image does not become LCP.
 */
export function DecorativeImage({
  src,
  className,
}: {
  src: string;
  className?: string;
}) {
  return (
    // eslint-disable-next-line @next/next/no-img-element -- intentional for LCP
    <img
      src={src}
      alt=""
      aria-hidden
      loading="lazy"
      decoding="async"
      fetchPriority="low"
      className={className}
    />
  );
}