export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
export interface PaginationQuery {
  page?: number;
  page_size?: number;
}
export type SearchParams = Record<string, string | string[] | undefined>;
