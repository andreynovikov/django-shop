import { APIRequestContext, expect } from '@playwright/test'

import type { Category, PaginatedResult, ProductInfo, Store } from '@/lib/types'

// Catalog data changes over time, so tests look up suitable products instead of hardcoding them
export async function findSewingMachines(request: APIRequestContext, filters: Record<string, string> = {}) {
  const categoryResponse = await request.get('/api/v0/categories/sewing_machines/')
  expect(categoryResponse.ok()).toBeTruthy()
  const category = await categoryResponse.json() as Category

  const params = new URLSearchParams({ categories: category.id.toString(), enabled: 'true', page_size: '50', ...filters })
  const productsResponse = await request.get(`/api/v0/products/?${params}`)
  expect(productsResponse.ok()).toBeTruthy()
  const { results } = await productsResponse.json() as PaginatedResult<ProductInfo>

  return results.filter(product => product.cost > 0)
}

async function loadProductStock(request: APIRequestContext, id: number) {
  const response = await request.get(`/api/v0/products/${id}/stock/`)
  expect(response.ok()).toBeTruthy()
  // ProductStock hides store 295
  return (await response.json() as Store[]).filter(store => store.id !== 295)
}

export async function findProductInStores(request: APIRequestContext) {
  for (const product of await findSewingMachines(request, { instock: '1' })) {
    const stores = await loadProductStock(request, product.id)
    if (stores.length > 0)
      return { product, store: stores[0] }
  }
  return undefined
}
