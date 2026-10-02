import { ServiceCenter } from '@/lib/types'
import { apiFetch } from './fetch'

export const serviceCenterKeys = {
  all: ['serviceCenters'],
  lists: () => [...serviceCenterKeys.all, 'list'],
  details: () => [...serviceCenterKeys.all, 'detail'],
  detail: (id: number) => [...serviceCenterKeys.details(), id],
}

export async function loadServiceCenters() {
  return await apiFetch<ServiceCenter[]>('servicecenters/')
}

export async function loadServiceCenter(id: number) {
  return await apiFetch<ServiceCenter>(`servicecenters/${id}/`)
}