"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { uploadLmsLearningMaterial } from "@/features/college-admin/api/lms-content";
import { collegeAdminQueryKeys } from "@/features/college-admin/query-keys";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  materialKind: "document" | "video";
  dialogTitle: string;
};

export function LmsContentUploadDialog({ open, onOpenChange, materialKind, dialogTitle }: Props) {
  const queryClient = useQueryClient();
  const [courseCode, setCourseCode] = useState("");
  const [title, setTitle] = useState("");
  const [unitNo, setUnitNo] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setCourseCode("");
    setTitle("");
    setUnitNo("");
    setFile(null);
    setError(null);
  }, []);

  const handleClose = useCallback(() => {
    if (busy) return;
    reset();
    onOpenChange(false);
  }, [busy, onOpenChange, reset]);

  const handleSubmit = useCallback(async () => {
    if (!file || !courseCode.trim() || !title.trim()) {
      setError("Course code, title and file are required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await uploadLmsLearningMaterial({
        course_code: courseCode.trim(),
        title: title.trim(),
        unit_no: unitNo.trim() ? Number(unitNo) : undefined,
        material_kind: materialKind,
        file,
      });
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.lmsLearningMaterialManagementPage() });
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.lmsVideoLectureManagementPage() });
      await queryClient.invalidateQueries({ queryKey: collegeAdminQueryKeys.lmsUnitChapterManagementPage() });
      handleClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }, [courseCode, file, handleClose, materialKind, queryClient, title, unitNo]);

  if (!open) return null;

  const accept = materialKind === "video" ? "video/*,.mp4,.webm,.mov" : ".pdf,.doc,.docx,.ppt,.pptx,.zip,image/*";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="lms-upload-title"
        className="w-full max-w-md rounded-xl border border-[#e8ecf2] bg-white p-5 shadow-lg"
      >
        <h3 id="lms-upload-title" className="text-[16px] font-semibold text-[#111827]">
          {dialogTitle}
        </h3>
        <p className="mt-1 text-[13px] text-[#6b7280]">
          Files are published to the selected course and appear in the learning materials list.
        </p>
        <div className="mt-4 space-y-3">
          <Input
            value={courseCode}
            onChange={(e) => setCourseCode(e.target.value)}
            placeholder="Course code (e.g. CS3401)"
            className="h-9 border-[#dce3ec] text-[13px]"
          />
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title"
            className="h-9 border-[#dce3ec] text-[13px]"
          />
          <Input
            value={unitNo}
            onChange={(e) => setUnitNo(e.target.value)}
            placeholder="Unit number (optional)"
            className="h-9 border-[#dce3ec] text-[13px]"
            inputMode="numeric"
          />
          <Input
            type="file"
            accept={accept}
            className="h-9 border-[#dce3ec] text-[13px] file:mr-2 file:rounded file:border-0 file:bg-[#f3f4f6] file:px-2 file:text-[12px]"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          {error ? <p className="text-[12px] text-[#b91c1c]">{error}</p> : null}
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <Button type="button" variant="outline" className="h-9 text-xs" disabled={busy} onClick={handleClose}>
            Cancel
          </Button>
          <Button type="button" className="h-9 bg-[#245dd8] text-xs hover:bg-[#1f4fb8]" disabled={busy} onClick={() => void handleSubmit()}>
            {busy ? "Uploading…" : "Upload"}
          </Button>
        </div>
      </div>
    </div>
  );
}