import { PaginatedResult, Product, ProductInfo, ProductStock } from '@/lib/types'
import { productSearchParamsSerializer, ProductSearchParamsType } from '@/lib/search-params'
import { apiFetch } from './fetch'

export const productKeys = {
  all: ['products'],
  fields: () => [...productKeys.all, 'fields'],
  suggestions: (text: string) => [...productKeys.all, 'suggestions', text],
  search: (text: string, filters: ProductSearchParamsType, ordering: string) => [...productKeys.all, { text, filters, ordering }],
  images: (id: number) => [...productKeys.all, id, 'images'],
  stock: (id: number) => [...productKeys.all, id, 'stock'],
  lists: () => [...productKeys.all, 'list'],
  list: (page: number, size: number, filters: ProductSearchParamsType, ordering: string) => [...productKeys.lists(), { page, size, filters, ordering }],
  details: () => [...productKeys.all, 'detail'],
  detail: (id: number) => [...productKeys.details(), id],
  info: (id: number) => [...productKeys.details(), id]
}

export async function loadProducts(page: number, page_size: number, filters: ProductSearchParamsType, ordering: string) {
  const url = 'products/' + productSearchParamsSerializer({
    ...filters,
    page,
    page_size,
    ordering,
  })
  return await apiFetch<PaginatedResult<ProductInfo>>(url)
}

/**
 * @deprecated Use `loadProducts` instead.
 */
export async function loadProductSuggestions(text: string) {
  const url = 'products/' + productSearchParamsSerializer({
    title: text,
    ta: 1,
    page_size: 10,
  })
  return await apiFetch<PaginatedResult<ProductInfo>>(url)
}

export async function getProductImages(id: number) {
  return await apiFetch<{ src: string }[]>(`products/${id}/images/`)
}

export async function loadProductStock(id: number) {
  return await apiFetch<ProductStock[]>(`products/${id}/stock/`)
}

export async function loadProduct(id: number) {
  return await apiFetch<Product>(`products/${id}/`)
}

export async function loadProductByCode(code: string) {
  return await apiFetch<Product>(`products/${code}/bycode/`)
}

export async function loadProductInfo(id: number) {
  return await apiFetch<ProductInfo>(`products/${id}/info/`)
}

export async function getProductFields() {
  return await apiFetch<Record<string, string>>('products/fields/')
}