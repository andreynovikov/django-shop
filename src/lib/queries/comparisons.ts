import { comparisonSearchParamsSerializer, kindSearchParamsSerializer, KindSearchParamsType } from '@/lib/search-params'
import { ProductKind } from '@/lib/types'
import { apiFetch } from './fetch'

export const comparisonKeys = {
  all: ['comparisons'],
  lists: () => [...comparisonKeys.all, 'list'],
  list: (kind: number | null) => [...comparisonKeys.lists(), kind]
}

export const kindKeys = {
  all: ['kinds'],
  lists: () => [...kindKeys.all, 'list'],
  list: (filter: KindSearchParamsType) => [...kindKeys.lists(), filter],
  details: () => [...kindKeys.all, 'detail'],
  detail: (id: number) => [...kindKeys.details(), id],
}

export async function loadComparisons(kind: number | null) {
  const url = 'comparisons/' + comparisonSearchParamsSerializer({ kind })
  return await apiFetch<number[]>(url)
}

export async function addToComparison(product: number) {
  return await apiFetch<number[]>('comparisons/add/', {
    body: { product }
  })
}

export async function removeFromComparison(product: number) {
  return await apiFetch<number[]>('comparisons/remove/', {
    body: { product }
  })
}

export async function loadKinds(productIds: number[]) {
  const url = 'kinds/' + kindSearchParamsSerializer({
    product: productIds,
  })
  return await apiFetch<ProductKind[]>(url)
}

export async function loadKind(id: number) {
  return await apiFetch<ProductKind>(`kinds/${id}/`)
}
