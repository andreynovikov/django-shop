import { blogEntrySearchParamsSerializer, BlogSearchParamsType } from '@/lib/search-params'
import { BlogCategory, BlogCloudTag, BlogEntry, BlogEntryInfo, PaginatedResult } from '@/lib/types'
import { apiFetch } from './fetch'

export const blogKeys = {
  all: ['blog'],
  lists: () => [...blogKeys.all, 'list'],
  list: (page: number | null, filters: BlogSearchParamsType) => [...blogKeys.lists(), { page, filters }],
  details: () => [...blogKeys.all, 'detail'],
  detail: (uri: string[]) => [...blogKeys.details(), uri],
  tags: () => [...blogKeys.lists(), 'tags'],
  categories: () => [...blogKeys.lists(), 'categories'],
  category: (idOrSlug: string | number) => [...blogKeys.categories(), idOrSlug],
}

export async function loadBlogTags() {
  return await apiFetch<BlogCloudTag[]>('blog/tags/')
}

export async function loadBlogCategories() {
  return await apiFetch<BlogCategory[]>('blog/categories/')
}

export async function loadBlogCategory(idOrSlug: string | number) {
  return await apiFetch<BlogCategory>(`blog/categories/${idOrSlug}/`)
}

export async function loadBlogEntries(page: number | null, filters: BlogSearchParamsType = {}) {
  const url = 'blog/entries/' + blogEntrySearchParamsSerializer({
    ...filters,
    page,
  })
  return await apiFetch<PaginatedResult<BlogEntryInfo>>(url)
}

export async function loadBlogEntry(uri: string[]) {
  return await apiFetch<BlogEntry>(`blog/entries/${uri.join('/')}/`)
}
