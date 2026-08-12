import { Integration, IntegrationProduct } from '@/lib/types'
import { apiFetch } from './fetch'

async function tokenizedFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  return await apiFetch<T>(endpoint, {
    ...options,
    headers: {
      'authorization': `Token ${process.env.API_TOKEN}`
    }
  })
}

export async function listIntegrations() {
  return await tokenizedFetch<Integration[]>('integrations/')
}

export async function retriveIntegration(id: number) {
  return await tokenizedFetch<Integration>(`integrations/${id}/`)
}

export async function retriveIntegrationByUtm(utm: string) {
  return await tokenizedFetch<Integration>(`integrations/${utm}/byutm/`)
}

export async function retriveIntegrationProducts(id: number) {
  return await tokenizedFetch<IntegrationProduct[]>(`integrations/${id}/products/`)
}
