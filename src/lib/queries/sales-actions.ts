import { ProductInfo, SalesAction } from '@/lib/types'
import { apiFetch } from './fetch'

export const salesActionKeys = {
  all: ['salesactions'],
  lists: () => [...salesActionKeys.all, 'list'],
  details: () => [...salesActionKeys.all, 'detail'],
  detail: (slug: string) => [...salesActionKeys.details(), slug],
  products: (slug: string) => [...salesActionKeys.detail(slug), 'products'],
}

export async function loadSalesActions() {
  return await apiFetch<SalesAction[]>('salesactions/')
};

export async function loadSalesAction(slug: string) {
  return await apiFetch<SalesAction>(`salesactions/${slug}/`)
}

export async function loadSalesActionProducts(slug: string) {
  return await apiFetch<ProductInfo[]>(`salesactions/${slug}/products/`)
}