import axios from 'axios'

import { Integration, IntegrationProduct } from './types'

const AXIOS_CONFIG = {
  baseURL: process.env.NEXT_PUBLIC_API,
  headers: {
    'Authorization': `Token ${process.env.API_TOKEN}`
  }
}

export const apiClient = axios.create(AXIOS_CONFIG)

export async function listIntegrations() {
  const response = await apiClient.get<Integration[]>('integrations/')
  return response.data
}

export async function retriveIntegration(id: number) {
  const response = await apiClient.get<Integration>(`integrations/${id}/`)
  return response.data
}

export async function retriveIntegrationByUtm(utm: string) {
  const response = await apiClient.get<Integration>(`integrations/${utm}/byutm/`)
  return response.data
}

export async function retriveIntegrationProducts(id: number) {
  const response = await apiClient.get<IntegrationProduct[]>(`integrations/${id}/products/`)
  return response.data
}
