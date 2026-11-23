"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { onCollegeAdminMutationError } from "@/features/college-admin/context/college-admin-validation-context";
import { toast } from "sonner";

import { ChevronLeftIcon } from "@/components/icons/erp/generated/chevron-left";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { QueryState } from "@/features/college-admin/components/ui/query-state";
import {
  useCreateStudentTransferRequest,
  useStudentTransferCreatePage,
} from "@/features/college-admin/hooks/use-student-transfer-create";

export function StudentTransferCreateDashboard() {
  const router = useRouter();
  const pageQuery = useStudentTransferCreatePage();
  const create = useCreateStudentTransferRequest();
  const data = pageQuery.data;

  const [studentRecordId, setStudentRecordId] = useState("");
  const [transferType, setTransferType] = useState<"programme" | "section" | "outgoing">("programme");
  const [toProgramme, setToProgramme] = useState("");
  const [toSection, setToSection] = useState("");
  const [toInstitution, setToInstitution] = useState("");
  const [effectiveSemester, setEffectiveSemester] = useState("");
  const [reason, setReason] = useState("");

  const submit = () => {
    if (!studentRecordId) {
      toast.error("Select a student.");
      return;
    }
    if (!reason.trim()) {
      toast.error("Enter a reason for the transfer.");
      return;
    }
    create.mutate(
      {
        student_record_id: studentRecordId,
        transfer_type: transferType,
        to_programme_code: toProgramme || undefined,
        to_section_code: toSection || undefined,
        to_institution_label: toInstitution || undefined,
        effective_semester: effectiveSemester || undefined,
        reason: reason.trim(),
      },
      {
        onSuccess: (res) => {
          toast.success("Transfer request submitted.");
          router.push(res.transfer_href);
        },
        onError: onCollegeAdminMutationError,
      },
    );
  };

  return (
    <div className="space-y-5" data-figma-frame="158:5236-create">
      <div className="flex items-center gap-2">
        <Link
          href={data?.back_href ?? "/college-admin/students/student-transfer-management"}
          className="inline-flex size-8 items-center justify-center rounded-md text-[#374151] hover:bg-[#f3f4f6]"
          aria-label={data?.back_label ?? "Back"}
        >
          <ChevronLeftIcon className="size-5" />
        </Link>
        <div>
          <h2 className="text-[20px] font-bold text-[#111827]">{data?.page_title ?? "New transfer request"}</h2>
          <p className="text-[13px] text-[#6b7280]">
            {data?.page_subtitle ?? "Create a programme, section, or outgoing transfer for review"}
          </p>
        </div>
      </div>

      <QueryState
        isLoading={pageQuery.isLoading}
        isError={pageQuery.isError}
        error={pageQuery.error}
        onRetry={() => void pageQuery.refetch()}
      >
        {data ? (
          <section className="mx-auto max-w-2xl overflow-hidden rounded-xl border border-[#e8ecf2] bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
            <div className="space-y-4 px-5 py-5">
              <div>
                <Label className="text-[12px] text-[#374151]">{data.student_field_label}</Label>
                <select
                  className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                  value={studentRecordId}
                  onChange={(e) => setStudentRecordId(e.target.value)}
                >
                  {data.student_options.map((opt) => (
                    <option key={opt.value || opt.label} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <Label className="text-[12px] text-[#374151]">{data.transfer_type_field_label}</Label>
                <select
                  className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                  value={transferType}
                  onChange={(e) => setTransferType(e.target.value as typeof transferType)}
                >
                  {data.transfer_type_options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {transferType !== "outgoing" ? (
                <div>
                  <Label className="text-[12px] text-[#374151]">{data.programme_field_label}</Label>
                  <select
                    className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                    value={toProgramme}
                    onChange={(e) => setToProgramme(e.target.value)}
                  >
                    {data.programme_options.map((opt) => (
                      <option key={opt.value || opt.label} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
              ) : null}

              {transferType === "section" ? (
                <div>
                  <Label className="text-[12px] text-[#374151]">{data.section_field_label}</Label>
                  <input
                    className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                    value={toSection}
                    onChange={(e) => setToSection(e.target.value)}
                    placeholder="e.g. A"
                  />
                </div>
              ) : null}

              {transferType === "outgoing" ? (
                <div>
                  <Label className="text-[12px] text-[#374151]">{data.institution_field_label}</Label>
                  <input
                    className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] px-3 text-[13px]"
                    value={toInstitution}
                    onChange={(e) => setToInstitution(e.target.value)}
                    placeholder="College or university name"
                  />
                </div>
              ) : null}

              <div>
                <Label className="text-[12px] text-[#374151]">{data.effective_field_label}</Label>
                <select
                  className="mt-1.5 h-9 w-full rounded-md border border-[#dce3ec] bg-white px-3 text-[13px]"
                  value={effectiveSemester}
                  onChange={(e) => setEffectiveSemester(e.target.value)}
                >
                  {data.effective_options.map((opt) => (
                    <option key={opt.value || opt.label} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <Label className="text-[12px] text-[#374151]">{data.reason_field_label}</Label>
                <textarea
                  className="mt-1.5 min-h-[88px] w-full rounded-md border border-[#dce3ec] px-3 py-2 text-[13px]"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Why is this transfer being requested?"
                />
              </div>

              <div className="flex flex-wrap gap-2 pt-2">
                <Button
                  type="button"
                  className="h-9 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]"
                  disabled={create.isPending}
                  onClick={submit}
                >
                  {data.submit_label}
                </Button>
                <Link
                  href={data.back_href}
                  className="inline-flex h-9 items-center rounded-md border border-[#dce3ec] px-4 text-xs font-medium text-[#374151] hover:bg-[#f9fafb]"
                >
                  Cancel
                </Link>
              </div>
            </div>
          </section>
        ) : null}
      </QueryState>
    </div>
  );
}