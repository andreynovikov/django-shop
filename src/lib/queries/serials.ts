import { Serial } from '@/lib/types'
import { apiFetch } from './fetch'

export const serialKeys = {
  all: ['serial'],
  lists: () => [...serialKeys.all, 'list'],
  details: () => [...serialKeys.all, 'detail'],
  detail: (id: number) => [...serialKeys.details(), id],
}

export async function createSerial(body: { number: string }) {
  return await apiFetch<Serial>('serials/', { body })
}