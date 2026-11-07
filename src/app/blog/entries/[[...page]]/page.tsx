import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import BlogEntryList from '@/components/blog/entry-list'

import { parsePageParam } from '@/lib/pagination'

import { getBlogEntries } from '@/app/blog/load'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Блог',
}

export default async function BlogEntriesPage({ params }: PageProps<'/blog/entries/[[...page]]'>) {
  const { page } = await params
  const pathname = '/blog/entries/'
  const currentPage = parsePageParam(page, pathname)
  const entries = await getBlogEntries(currentPage)

  return pageContentWrapper({
    title: 'Блог',
    children: (
      <div className="container mb-2 pb-12 md:mb-6">
        { /* TODO: add featured posts carousel */}
        <hr className="mt-12" />
        <BlogEntryList entries={entries} pathname={pathname} />
      </div>
    )
  })
}
