import { storeSearchParamsSerializer, StoreSearchParamsType } from '@/lib/search-params'
import { apiFetch } from './fetch'

export const storeKeys = {
  all: ['stores'],
  lists: () => [...storeKeys.all, 'list'],
  list: (filters: StoreSearchParamsType) => [...storeKeys.lists(), filters],
  details: () => [...storeKeys.all, 'detail'],
  detail: (id: number) => [...storeKeys.details(), id],
}

export async function loadStores(filters: StoreSearchParamsType = {}) {
  return await apiFetch('stores/' + storeSearchParamsSerializer(filters))
}

export async function loadStore(id: number) {
  return await apiFetch(`stores/${id}/`)
}
