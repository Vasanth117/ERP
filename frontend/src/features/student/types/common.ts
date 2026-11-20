export type ApiPage<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};