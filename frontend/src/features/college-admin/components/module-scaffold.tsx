import { PageHeading } from "@/features/college-admin/components/layout/page-heading";

type ModuleScaffoldProps = {
  title: string;
  figmaPage: string;
  description?: string;
  apiPrefix?: string;
};

/** Shell page for CA03–CA24 modules while frame-by-frame Figma parity is in progress. */
export function CollegeAdminModuleScaffold({
  title,
  figmaPage,
  description,
  apiPrefix,
}: ModuleScaffoldProps) {
  return (
    <div>
      <PageHeading
        title={title}
        description={
          description ??
          `Figma ${figmaPage} screens are wired in the College Admin shell. Implementation continues frame by frame.`
        }
      />
      <div className="rounded-xl border border-dashed border-[#dce3ec] bg-white p-8 text-sm text-[#607086]">
        <p>
          Tracked design module: <strong className="text-[#172b45]">{figmaPage}</strong>
        </p>
        {apiPrefix ? (
          <p className="mt-2">
            Backend API prefix:{" "}
            <code className="text-[#245dd8]">{apiPrefix}</code>
          </p>
        ) : null}
        <p className="mt-4">
          Navigation, layout, auth and API client are ready. The next pass maps each
          Figma frame in this module to routes following{" "}
          <code>FIGMA_TO_FRONTEND_IMPLEMENTATION_GUIDE.md</code>.
        </p>
      </div>
    </div>
  );
}