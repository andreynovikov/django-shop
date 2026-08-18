import { blogEntrySearchParamsSerializer, BlogSearchParamsType } from '@/lib/search-params'
import { apiFetch } from './fetch'

export const blogKeys = {
  all: ['blog'],
  lists: () => [...blogKeys.all, 'list'],
  list: (page: number | null, filters: BlogSearchParamsType) => [...blogKeys.lists(), { page, filters }],
  details: () => [...blogKeys.all, 'detail'],
  detail: (uri: string[]) => [...blogKeys.details(), uri],
  tags: () => [...blogKeys.lists(), 'tags'],
  categories: () => [...blogKeys.lists(), 'categories'],
  category: (slug: string) => [...blogKeys.categories(), slug],
}

export async function loadBlogTags() {
  return await apiFetch('blog/tags/')
}

export async function loadBlogCategories() {
  return await apiFetch('blog/categories/')
}

export async function loadBlogCategory(slug: string) {
  return await apiFetch(`blog/categories/${slug}/`)
}

export async function loadBlogEntries(page: number | null, filters: BlogSearchParamsType = {}) {
  const url = 'blog/entries/' + blogEntrySearchParamsSerializer({
    ...filters,
    page,
  })
  return await apiFetch(url)
}

export async function loadBlogEntry(uri: string[]) {
  return await apiFetch(`blog/entries/${uri.join('/')}/`)
}
