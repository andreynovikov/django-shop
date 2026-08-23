import { FlatPage, FlatPageInfo } from '@/lib/types'
import { apiFetch } from './fetch'

export const pageKeys = {
  all: ['pages'],
  lists: () => [...pageKeys.all, 'list'],
  details: () => [...pageKeys.all, 'detail'],
  detail: (uri: string[]) => [...pageKeys.details(), uri],
}

export async function loadPages() {
  return await apiFetch<FlatPageInfo[]>('pages/')
}

export async function loadPage(uri: string[]) {
  return await apiFetch<FlatPage>(`pages/${uri.join('/')}/`)
}