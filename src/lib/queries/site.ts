import { advertSearchParamsSerializer } from '@/lib/search-params'
import { Advert, News, Site } from '@/lib/types'
import { apiFetch } from './fetch'

export const newsKeys = {
  all: ['news'],
  lists: () => [...newsKeys.all, 'list'],
}

export const advertKeys = {
  all: ['adverts'],
  lists: () => [...advertKeys.all, 'list'],
  list: (places: string[]) => [...advertKeys.lists(), places]
}

export const siteKeys = {
  all: ['sites'],
  current: () => [...siteKeys.all, 'current'],
}

export async function loadNews() {
  return await apiFetch<News[]>('news/')
}

export async function loadAdverts(places: string[], categoryId = undefined) {
  const url = 'adverts/' + advertSearchParamsSerializer({
    category: categoryId,
    places,
  })
  return await apiFetch<Advert[]>(url)
}

export async function loadCurrentSite() {
  return await apiFetch<Site>('sites/current/')
}

export async function getWarrantyCard(code: string) {
  return await apiFetch<{ html: string }>(`warrantycard/${encodeURIComponent(code)}/`)
}