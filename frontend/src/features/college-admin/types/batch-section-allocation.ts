import type { BatchSectionAllocationField } from "@/features/college-admin/types/batch-section-configuration";

export type BatchSectionAllocationSectionRow = {
  section_id: string;
  section_label: string;
  programme_label: string;
  semester_label: string;
  strength_count: number;
  capacity_count: number;
  status_label: string;
  status_tone: string;
};

export type BatchSectionAllocationUnallocatedRow = {
  record_id: string;
  student_name: string;
  register_number: string;
  programme_label: string;
  detail_href: string;
};

export type BatchSectionAllocationPage = {
  page_title: string;
  page_subtitle: string;
  auto_allocate_label: string;
  confirm_label: string;
  section_strength_title: string;
  section_summary_label: string;
  section_table_headers: string[];
  section_rows: BatchSectionAllocationSectionRow[];
  section_pagination: PaginationBlock;
  allocation_rules_title: string;
  allocation_rules_fields: BatchSectionAllocationField[];
  unallocated_title: string;
  unallocated_summary_label: string;
  unallocated_table_headers: string[];
  unallocated_rows: BatchSectionAllocationUnallocatedRow[];
  unallocated_pagination: PaginationBlock;
  updated_at_label: string;
  footer_disclaimer: string;
  footer_snapshot_label: string;
  generated_at: string;
};

type PaginationBlock = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type BatchSectionAllocationPageQuery = {
  section_page?: number;
  unallocated_page?: number;
};

export type BatchSectionAllocationRulesPayload = {
  allocation_method: string;
  max_per_section: number;
  keep_groups_together: string;
  section_page?: number;
  unallocated_page?: number;
};