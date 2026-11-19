import Image from "next/image";

export function CollegeAdminIcon({
  name,
  size = 16,
  className,
}: {
  name: string;
  size?: number;
  className?: string;
}) {
  return (
    <Image
      src={`/college-admin/icons/${name}.svg`}
      alt=""
      width={size}
      height={size}
      className={className ?? "size-4 shrink-0"}
    />
  );
}