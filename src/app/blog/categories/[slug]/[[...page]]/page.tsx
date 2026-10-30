import { cache } from 'react'
import { Metadata } from 'next'
import { notFound } from 'next/navigation'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import BlogEntryList from '@/components/blog/entry-list'

import { HttpError, loadBlogCategory } from '@/lib/queries'
import { parsePageParam } from '@/lib/pagination'

import { getBlogEntries } from '@/app/blog/load'

export const dynamic = 'force-dynamic'

// Shared by generateMetadata and the page, so the category is fetched once per render
const getCategory = cache(async (slug: string) => {
  try {
    return await loadBlogCategory(slug)
  } catch (err) {
    if (err instanceof HttpError && err.status === 404)
      notFound()
    throw err
  }
})

export async function generateMetadata({ params }: PageProps<'/blog/categories/[slug]/[[...page]]'>): Promise<Metadata> {
  const { slug } = await params
  const category = await getCategory(slug)
  return { title: `Архив категории ${category.title}` }
}

export default async function BlogCategoryPage({ params }: PageProps<'/blog/categories/[slug]/[[...page]]'>) {
  const { slug: encodedSlug, page } = await params
  // unlike generateMetadata, the page gets percent-encoded params
  const slug = decodeURIComponent(encodedSlug)
  const pathname = `/blog/categories/${encodeURIComponent(slug)}/`
  const currentPage = parsePageParam(page, pathname)
  const category = await getCategory(slug)
  const entries = await getBlogEntries(currentPage, { categories: category.id })

  return pageContentWrapper({
    title: `Архив категории ${category.title}`,
    children: (
      <div className="container pb-5 mb-2 mb-md-4">
        <BlogEntryList entries={entries} pathname={pathname} />
      </div>
    )
  })
}
