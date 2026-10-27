import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import BlogEntryList from '@/components/blog/entry-list'

import { parsePageParam } from '@/lib/pagination'

import { getBlogEntries } from '@/app/blog/load'

export const dynamic = 'force-dynamic'

export async function generateMetadata({ params }: PageProps<'/blog/tags/[tag]/[[...page]]'>): Promise<Metadata> {
  const { tag } = await params
  return { title: `Архив по тэгу '${tag}'` }
}

export default async function BlogTagPage({ params }: PageProps<'/blog/tags/[tag]/[[...page]]'>) {
  const { tag: encodedTag, page } = await params
  // unlike generateMetadata, the page gets percent-encoded params
  const tag = decodeURIComponent(encodedTag)
  const pathname = `/blog/tags/${encodeURIComponent(tag)}/`
  const currentPage = parsePageParam(page, pathname)
  const entries = await getBlogEntries(currentPage, { tags: tag })

  return pageContentWrapper({
    title: `Архив по тэгу '${tag}'`,
    children: (
      <div className="container pb-5 mb-2 mb-md-4">
        <BlogEntryList entries={entries} pathname={pathname} />
      </div>
    )
  })
}
