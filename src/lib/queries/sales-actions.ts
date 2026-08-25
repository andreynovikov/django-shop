import { PaginatedResult, ProductInfo, SalesAction } from '@/lib/types'
import { salesActionProductsSearchParamsSerializer } from '@/lib/search-params'
import { apiFetch } from './fetch'

export const salesActionKeys = {
  all: ['salesactions'],
  lists: () => [...salesActionKeys.all, 'list'],
  details: () => [...salesActionKeys.all, 'detail'],
  detail: (slug: string) => [...salesActionKeys.details(), slug],
  products: (slug: string, page: number | null) => [...salesActionKeys.detail(slug), 'products', page],
}

export async function loadSalesActions() {
  return await apiFetch<SalesAction[]>('salesactions/')
};

export async function loadSalesAction(slug: string) {
  return await apiFetch<SalesAction>(`salesactions/${slug}/`)
}

export async function loadSalesActionProducts(slug: string, page: number | null) {
  const url = `salesactions/${slug}/products/` + salesActionProductsSearchParamsSerializer({
    page,
    page_size: 16,
  })
  return await apiFetch<PaginatedResult<ProductInfo>>(url)
}