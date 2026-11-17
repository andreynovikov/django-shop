import { ServiceCenter } from '@/lib/types'
import { cacheTags, tagged } from './cache-tags'
import { apiFetch } from './fetch'

export const serviceCenterKeys = {
  all: ['serviceCenters'],
  lists: () => [...serviceCenterKeys.all, 'list'],
  details: () => [...serviceCenterKeys.all, 'detail'],
  detail: (id: number) => [...serviceCenterKeys.details(), id],
}

export async function loadServiceCenters() {
  return await apiFetch<ServiceCenter[]>('servicecenters/', tagged(cacheTags.serviceCenters))
}

export async function loadServiceCenter(id: number) {
  return await apiFetch<ServiceCenter>(`servicecenters/${id}/`)
}