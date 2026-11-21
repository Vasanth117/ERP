import { apiRequest } from "@/lib/api/client";

const BASE = "/students";

export type StudentRecordDocument = {
  document_id: string;
  title: string;
  category: string;
  uploaded_at: string | null;
  verified: boolean;
  file_format: string;
  download_available: boolean;
  source: string;
};

export type StudentRecordDocumentDownload = {
  document_id: string;
  document_type: string;
  download_token: string;
  expires_at: string;
  file_name?: string | null;
};

export type StudentRecordDocumentBulkDownload = {
  items: StudentRecordDocumentDownload[];
};

export function fetchStudentRecordDocuments() {
  return apiRequest<StudentRecordDocument[]>(`${BASE}/me/documents/record`);
}

export function fetchStudentRecordDocumentDownloadToken(documentId: string) {
  return apiRequest<StudentRecordDocumentDownload>(
    `${BASE}/me/documents/${encodeURIComponent(documentId)}/download-token`,
  );
}

export function fetchStudentRecordDocumentsDownloadAll() {
  return apiRequest<StudentRecordDocumentBulkDownload>(`${BASE}/me/documents/record/download-all`);
}