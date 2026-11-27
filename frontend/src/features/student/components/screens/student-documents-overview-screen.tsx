"use client";

import { useMemo, useState } from "react";

import { CollegeAdminIcon } from "@/features/college-admin/components/layout/college-admin-icon";
import type { StudentRecordDocument } from "@/features/student/api/student-record-documents";
import {
  ProfilePageHeading,
  ProfilePanel,
} from "@/features/student/components/ui/student-profile-ui";
import { QueryState } from "@/features/student/components/ui/student-screen-ui";
import {
  useStudentRecordDocumentDownload,
  useStudentRecordDocuments,
  useStudentRecordDocumentsDownloadAll,
} from "@/features/student/hooks/use-student-record-documents";
import { STUDENT_BTN_PRIMARY } from "@/features/student/components/ui/student-portal-tokens";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 5;

function formatUploaded(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

function categoryLabel(category: string): string {
  if (!category) return "—";
  return category.charAt(0).toUpperCase() + category.slice(1);
}

/** ST 01.10 — Student Documents Overview (read-only, node 164:2942). */
export function StudentDocumentsOverviewScreen() {
  const docs = useStudentRecordDocuments();
  const downloadOne = useStudentRecordDocumentDownload();
  const downloadAll = useStudentRecordDocumentsDownloadAll();
  const [page, setPage] = useState(0);
  const [notice, setNotice] = useState<string | null>(null);

  const total = docs.data?.length ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const slice = useMemo(() => {
    const rows = docs.data ?? [];
    const start = page * PAGE_SIZE;
    return rows.slice(start, start + PAGE_SIZE);
  }, [docs.data, page]);

  const downloadableCount = (docs.data ?? []).filter((d) => d.download_available).length;

  async function handleDownload(row: StudentRecordDocument) {
    setNotice(null);
    if (!row.download_available) {
      setNotice(`${row.title} is view-only on your record. Contact the college for a copy.`);
      return;
    }
    try {
      const result = await downloadOne.mutateAsync(row.document_id);
      const label = result.file_name ? ` (${result.file_name})` : "";
      setNotice(`Download prepared for ${row.title}${label}. Token expires at ${formatUploaded(result.expires_at)}.`);
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Could not prepare download.");
    }
  }

  async function handleDownloadAll() {
    setNotice(null);
    if (downloadableCount === 0) {
      setNotice("No downloadable documents on your record yet.");
      return;
    }
    try {
      const bundle = await downloadAll.mutateAsync();
      setNotice(
        `Prepared ${bundle.items.length} download link${bundle.items.length === 1 ? "" : "s"} (valid 15 minutes).`,
      );
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Could not prepare downloads.");
    }
  }

  return (
    <div className="space-y-5" data-figma-node="164:2942">
      <ProfilePageHeading
        title="Student Documents Overview"
        description="Documents on your record"
        actions={
          <button
            type="button"
            disabled={downloadAll.isPending || docs.isLoading}
            onClick={() => void handleDownloadAll()}
            className={cn(
              STUDENT_BTN_PRIMARY,
              (downloadAll.isPending || docs.isLoading) && "opacity-60",
            )}
          >
            <CollegeAdminIcon name="download" size={14} className="text-white" />
            {downloadAll.isPending ? "Preparing…" : "Download all"}
          </button>
        }
      />

      <QueryState
        query={docs}
        isLoading={docs.isLoading}
        isError={docs.isError}
        error={docs.error}
        onRetry={() => void docs.refetch()}
        isEmpty={!total}
        emptyMessage="No documents on your record yet."
      >
        {total > 0 ? (
          <ProfilePanel
            title="Documents"
            action={
              <span className="text-[11px] font-normal text-[#8a98aa]">
                {Math.min(PAGE_SIZE, slice.length)} of {total}
              </span>
            }
          >
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-[12px]">
                <thead>
                  <tr className="border-b border-[#eef2f6] text-[11px] font-semibold text-[#8a98aa]">
                    <th className="pb-2 pr-3 font-semibold">Document</th>
                    <th className="pb-2 pr-3 font-semibold">Category</th>
                    <th className="pb-2 pr-3 font-semibold">Uploaded</th>
                    <th className="pb-2 pr-3 font-semibold">Verified</th>
                    <th className="pb-2 pr-3 font-semibold">Format</th>
                    <th className="pb-2 text-right font-semibold"> </th>
                  </tr>
                </thead>
                <tbody>
                  {slice.map((row) => (
                    <tr key={row.document_id} className="border-b border-[#f1f5f9] last:border-0">
                      <td className="py-3 pr-3 font-medium text-[#172b45]">{row.title}</td>
                      <td className="py-3 pr-3 text-[#607086]">{categoryLabel(row.category)}</td>
                      <td className="py-3 pr-3 text-[#607086]">{formatUploaded(row.uploaded_at)}</td>
                      <td className="py-3 pr-3">
                        {row.verified ? (
                          <VerifiedBadge />
                        ) : (
                          <span className="text-[11px] text-[#8a98aa]">Pending</span>
                        )}
                      </td>
                      <td className="py-3 pr-3 text-[#607086]">{row.file_format}</td>
                      <td className="py-3 text-right">
                        {row.download_available ? (
                          <button
                            type="button"
                            className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#245dd8] hover:underline"
                            disabled={downloadOne.isPending}
                            onClick={() => void handleDownload(row)}
                          >
                            <CollegeAdminIcon name="download" size={12} />
                            Download
                          </button>
                        ) : (
                          <span className="text-[11px] text-[#8a98aa]">View only</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {pageCount > 1 ? (
              <div className="mt-4 flex items-center justify-between border-t border-[#eef2f6] pt-3">
                <button
                  type="button"
                  disabled={page === 0}
                  className="text-[11px] font-semibold text-[#245dd8] disabled:text-[#cbd5e1]"
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                >
                  Previous
                </button>
                <span className="text-[11px] text-[#8a98aa]">
                  Page {page + 1} of {pageCount}
                </span>
                <button
                  type="button"
                  disabled={page >= pageCount - 1}
                  className="text-[11px] font-semibold text-[#245dd8] disabled:text-[#cbd5e1]"
                  onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
                >
                  Next
                </button>
              </div>
            ) : null}

            {notice ? (
              <p className="mt-3 text-[12px] text-[#047857]" role="status">
                {notice}
              </p>
            ) : null}

            <p className="mt-4 text-[11px] text-[#8a98aa]">
              Read-only access. Uploads and verification are managed by the college. You cannot change records here.
            </p>
          </ProfilePanel>
        ) : null}
      </QueryState>
    </div>
  );
}

function VerifiedBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded bg-[#e7f6ed] px-1.5 py-0.5 text-[11px] font-semibold text-[#1f7a45]">
      <CollegeAdminIcon name="check" size={12} className="text-[#1f7a45]" />
      Verified
    </span>
  );
}