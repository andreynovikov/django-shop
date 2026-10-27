import { cache } from 'react'
import { Metadata } from 'next'
import Link from 'next/link'
import { notFound, redirect } from 'next/navigation'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import BlogEntryAuthor from '@/components/blog/entry-author'
import Tooltip from '@/components/ui/tooltip'

import { HttpError, loadBlogEntry } from '@/lib/queries'
import { BlogEntryNavigation } from '@/lib/types'

export const dynamic = 'force-dynamic'

// Shared by generateMetadata and the page, so the entry is fetched once per render
const getEntry = cache(async (uri: string[]) => {
  try {
    const entry = await loadBlogEntry(uri)
    // backend returns an empty entry instead of 404 for unknown uri
    if (entry?.id)
      return entry
  } catch (err) {
    if (!(err instanceof HttpError && err.status === 404))
      throw err
  }
  notFound()
})

export async function generateMetadata({ params }: PageProps<'/blog/[...entry]'>): Promise<Metadata> {
  const { entry: uri } = await params
  const entry = await getEntry(uri)
  return { title: entry.title }
}

const navigationPopover = (neighbour: BlogEntryNavigation) => (
  <>
    <h6 className="fs-sm fw-semibold mb-0">
      {neighbour.title}
    </h6>
    <span className="d-block fs-xs text-muted">
      {neighbour.author.full_name}
    </span>
  </>
)

export default async function BlogEntryPage({ params }: PageProps<'/blog/[...entry]'>) {
  const { entry: encodedUri } = await params
  // unlike generateMetadata, the page gets percent-encoded params
  const uri = encodedUri.map(decodeURIComponent)
  const entry = await getEntry(uri)

  // short uri of old links
  if (uri.length === 1)
    redirect(entry.urls.canonical)

  return pageContentWrapper({
    title: entry.title,
    children: (
      <div className="container pb-5">
        <div className="row justify-content-center pt-5 mt-md-2">
          <div className="col-lg-9">
            <div className="d-flex flex-wrap justify-content-between align-items-center pb-4 mt-n1">
              <div className="d-flex align-items-center fs-sm mb-2">
                <BlogEntryAuthor entry={entry} wide />
              </div>
            </div>
            <div dangerouslySetInnerHTML={{ __html: entry.content }}></div>
            <div className="d-flex flex-wrap justify-content-between pt-2 pb-4 mb-1">
              <div className="mt-3 me-3">
                {entry.tags && entry.tags.map((tag) => (
                  <Link className="btn-tag me-2 mb-2" href={`/blog/tags/${encodeURIComponent(tag)}/`} key={tag}>
                    #{tag}
                  </Link>
                ))}
              </div>
            </div>
            <nav className="entry-navigation" aria-label="Навигация по записям">
              {entry.navigation.previous && (
                <Tooltip popover content={navigationPopover(entry.navigation.previous)}>
                  <Link className="entry-navigation-link" href={entry.navigation.previous.urls.canonical}>
                    <i className="ci-arrow-left me-2" />
                    <span className="d-none d-sm-inline">Предыдущая запись</span>
                  </Link>
                </Tooltip>
              )}
              <Link className="entry-navigation-link" href="/blog/entries/">
                <i className="ci-view-list me-2" />
                <span className="d-none d-sm-inline">Все записи</span>
              </Link>
              {entry.navigation.next && (
                <Tooltip popover content={navigationPopover(entry.navigation.next)}>
                  <Link className="entry-navigation-link" href={entry.navigation.next.urls.canonical}>
                    <span className="d-none d-sm-inline">Следующая запись</span>
                    <i className="ci-arrow-right ms-2" />
                  </Link>
                </Tooltip>
              )}
            </nav>
          </div>
        </div>
      </div>
    )
  })
}
