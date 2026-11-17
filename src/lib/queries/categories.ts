import { categorySearchParamsSerializer, CategorySearchParamsType } from '@/lib/search-params'
import { Category, CategoryTree } from '@/lib/types'
import { cacheTags, tagged } from './cache-tags'
import { apiFetch } from './fetch'

export const categoryKeys = {
  all: ['categories'],
  lists: () => [...categoryKeys.all, 'list'],
  details: () => [...categoryKeys.all, 'detail'],
  detail: (path: string[]) => [...categoryKeys.details(), path],
}

export async function loadCategories(filters: CategorySearchParamsType = {}) {
  return await apiFetch<CategoryTree>('categories/' + categorySearchParamsSerializer(filters), tagged(cacheTags.catalog))
}

export async function loadCategory(path: string[]) {
  return await apiFetch<Category>(`categories/${path.join('/')}/`, tagged(cacheTags.categoryPath(path)))
}
