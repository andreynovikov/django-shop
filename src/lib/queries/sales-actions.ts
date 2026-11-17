import { PaginatedResult, ProductInfo, SalesAction } from '@/lib/types'
import { salesActionProductsSearchParamsSerializer } from '@/lib/search-params'
import { cacheTags, tagged } from './cache-tags'
import { apiFetch } from './fetch'

export const salesActionKeys = {
  all: ['salesactions'],
  lists: () => [...salesActionKeys.all, 'list'],
  details: () => [...salesActionKeys.all, 'detail'],
  detail: (slug: string) => [...salesActionKeys.details(), slug],
  products: (slug: string, page: number | null) => [...salesActionKeys.detail(slug), 'products', page],
}

export async function loadSalesActions() {
  return await apiFetch<SalesAction[]>('salesactions/', tagged(cacheTags.actions))
};

export async function loadSalesAction(slug: string) {
  return await apiFetch<SalesAction>(`salesactions/${slug}/`, tagged(cacheTags.action(slug)))
}

export async function loadSalesActionProducts(slug: string, page: number | null) {
  const url = `salesactions/${slug}/products/` + salesActionProductsSearchParamsSerializer({
    page,
    page_size: 16,
  })
  return await apiFetch<PaginatedResult<ProductInfo>>(url, tagged(cacheTags.action(slug)))
}