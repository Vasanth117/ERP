export type LibraryBookCatalogueRow = {
  book_id: string;
  title: string;
  isbn_label: string;
  author_label: string;
  category_label: string;
  copies_label: string;
  available_label: string;
  detail_href: string;
};

export type LibraryBookCataloguePagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  page_numbers: number[];
  has_previous: boolean;
  has_next: boolean;
};

export type LibraryFilterOption = { value: string; label: string };

export type LibraryBookCataloguePage = {
  page_title: string;
  page_subtitle: string;
  export_label: string;
  add_title_label: string;
  add_title_href: string;
  search_placeholder: string;
  category_filter_label: string;
  branch_filter_label: string;
  category_options: LibraryFilterOption[];
  branch_options: LibraryFilterOption[];
  catalogue_section_title: string;
  table_headers: string[];
  catalogue_rows: LibraryBookCatalogueRow[];
  empty_table_message: string;
  showing_label: string;
  pagination: LibraryBookCataloguePagination;
  generated_at: string;
};

export type LibraryBookCataloguePageQuery = {
  page?: number;
  page_size?: number;
  search?: string;
  category?: string;
  branch_code?: string;
};