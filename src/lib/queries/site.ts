import { advertSearchParamsSerializer } from '@/lib/search-params'
import { Advert, News, Site } from '@/lib/types'
import { cacheTags, tagged } from './cache-tags'
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
  return await apiFetch<News[]>('news/', tagged(cacheTags.news))
}

export async function loadAdverts(places: string[], categoryId?: number) {
  const url = 'adverts/' + advertSearchParamsSerializer({
    category: categoryId,
    places,
  })
  return await apiFetch<Advert[]>(url, tagged(...places.map(cacheTags.adverts)))
}

export async function loadCurrentSite() {
  return await apiFetch<Site>('sites/current/', tagged(cacheTags.site))
}

export async function getWarrantyCard(code: string) {
  return await apiFetch<{ html: string }>(`warrantycard/${encodeURIComponent(code)}/`)
}