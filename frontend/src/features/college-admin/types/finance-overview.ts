import type { AcademicTermSummary } from "@/features/college-admin/types/dashboard";

export type FinanceOverviewQuery = {
  academic_year_label?: string;
  programme_code?: string;
  fee_head?: string;
};

export type FinanceOverviewKpi = {
  total_demand_inr: number;
  student_count: number;
  fee_head_count: number;
  collected_inr: number;
  collected_pct: number | null;
  outstanding_inr: number;
  students_with_dues: number;
  scholarships_concessions_inr: number;
  scholarship_beneficiaries: number;
};

export type FinanceMonthlyCollectionPoint = {
  year: number;
  month: number;
  label: string;
  amount_inr: number;
  is_month_to_date: boolean;
};

export type FinanceProgrammeDuesRow = {
  bucket_key: string;
  label: string;
  demand_amount: number;
  collected_amount: number;
  outstanding_amount: number;
  students_with_dues: number;
  collection_pct: number | null;
  status_key: string;
  status_label: string;
};

export type FinancePaymentModeItem = {
  mode_key: string;
  label: string;
  share_pct: number | null;
  amount_inr: number;
};

export type FinanceAttentionItem = {
  item_key: string;
  label: string;
  count: number;
};

export type FinanceScholarshipDisbursementItem = {
  program_label: string;
  amount_inr: number;
};

export type FinanceOverview = {
  filters: {
    academic_year_label: string | null;
    programme_code: string | null;
    fee_head: string | null;
  };
  academic_term: AcademicTermSummary;
  academic_year_display: string | null;
  kpis: FinanceOverviewKpi;
  monthly_collection: FinanceMonthlyCollectionPoint[];
  programme_dues_rows: FinanceProgrammeDuesRow[];
  collection_target_pct: number;
  payment_modes: FinancePaymentModeItem[];
  attention_items: FinanceAttentionItem[];
  scholarship_disbursements: FinanceScholarshipDisbursementItem[];
  fee_head_options: string[];
  generated_at: string;
};