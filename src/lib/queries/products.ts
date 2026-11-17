import { PaginatedResult, Product, ProductInfo, ProductList, StoreInfo } from '@/lib/types'
import { productFieldsSerializer, productSearchParamsSerializer, ProductSearchParamsType } from '@/lib/search-params'
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
  // pages loaded one after another from firstPage on, for useInfiniteQuery
  listPages: (firstPage: number, size: number, filters: ProductSearchParamsType, ordering: string) => [...productKeys.lists(), 'pages', { firstPage, size, filters, ordering }],
  details: () => [...productKeys.all, 'detail'],
  detail: (id: number) => [...productKeys.details(), id],
  info: (id: number) => [...productKeys.details(), id]
}

// With fields, only those fields of each product, e.g. the codes for the sitemap: a much smaller answer that the
// backend makes faster. The plain signature is last, so Parameters<typeof loadProducts> is its own.
export async function loadProducts<Field extends keyof ProductInfo>(page: number | null, page_size: number, filters: ProductSearchParamsType, ordering: string, fields: Field[]): Promise<PaginatedResult<Pick<ProductInfo, Field>>>
export async function loadProducts(page: number | null, page_size: number, filters: ProductSearchParamsType, ordering: string): Promise<ProductList>
export async function loadProducts(page: number | null, page_size: number, filters: ProductSearchParamsType, ordering: string, fields?: (keyof ProductInfo)[]) {
  let url = 'products/' + productSearchParamsSerializer({
    ...filters,
    page,
    page_size,
    ordering,
  })
  if (fields)
    url = productFieldsSerializer(url, { fields })
  return await apiFetch<ProductList>(url)
}

/**
 * @deprecated Use `loadProducts` instead.
 */
export async function loadProductSuggestions(text: string) {
  const url = 'products/' + productSearchParamsSerializer({
    title: text,
    ta: 1,
    page_size: 10,
    enabled: true,
  })
  // with ta=1 the backend returns product titles instead of products
  return await apiFetch<PaginatedResult<string>>(url)
}

export async function getProductImages(id: number) {
  return await apiFetch<{ src: string }[]>(`products/${id}/images/`)
}

export async function loadProductStock(id: number) {
  return await apiFetch<StoreInfo[]>(`products/${id}/stock/`)
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