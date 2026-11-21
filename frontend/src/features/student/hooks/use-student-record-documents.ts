import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchStudentRecordDocumentDownloadToken,
  fetchStudentRecordDocuments,
  fetchStudentRecordDocumentsDownloadAll,
} from "@/features/student/api/student-record-documents";
import { studentQueryKeys } from "@/features/student/query-keys";

export function useStudentRecordDocuments() {
  return useQuery({
    queryKey: studentQueryKeys.recordDocuments(),
    queryFn: fetchStudentRecordDocuments,
  });
}

export function useStudentRecordDocumentDownload() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: fetchStudentRecordDocumentDownloadToken,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: studentQueryKeys.recordDocuments() });
    },
  });
}

export function useStudentRecordDocumentsDownloadAll() {
  return useMutation({
    mutationFn: fetchStudentRecordDocumentsDownloadAll,
  });
}