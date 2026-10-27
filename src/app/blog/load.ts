import { notFound } from 'next/navigation'

import { HttpError, loadBlogEntries } from '@/lib/queries'
import { BlogSearchParamsType } from '@/lib/search-params'

export async function getBlogEntries(page: number, filters: BlogSearchParamsType = {}) {
  try {
    return await loadBlogEntries(page, filters)
  } catch (err) {
    // backend returns 404 for pages beyond the last one
    if (err instanceof HttpError && err.status === 404)
      notFound()
    throw err
  }
}
