import { blogEntrySearchParamsSerializer, BlogSearchParamsType } from '@/lib/search-params'
import { BlogCategory, BlogCloudTag, BlogEntry, BlogEntryInfo, PaginatedResult } from '@/lib/types'
import { apiFetch } from './fetch'

export async function loadBlogTags() {
  return await apiFetch<BlogCloudTag[]>('blog/tags/')
}

export async function loadBlogCategories() {
  return await apiFetch<BlogCategory[]>('blog/categories/')
}

export async function loadBlogCategory(slug: string) {
  return await apiFetch<BlogCategory>(`blog/categories/${slug}/`)
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
