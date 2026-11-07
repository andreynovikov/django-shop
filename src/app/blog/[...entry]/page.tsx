import { cache } from 'react'
import { Metadata } from 'next'
import Link from 'next/link'
import { notFound, redirect } from 'next/navigation'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import BlogEntryAuthor from '@/components/blog/entry-author'
import Tooltip from '@/components/ui/tooltip'

import { HttpError, loadBlogEntry } from '@/lib/queries'
import { BlogEntryNavigation } from '@/lib/types'
import { contentClass } from '@/components/ui/content'
import { tagClass } from '@/components/ui/widget'
import { IconChevronLeft, IconChevronRight, IconList } from '@tabler/icons-react'

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

// Links to the previous entry, all entries and the next entry, in equal parts of a bordered bar
const navigationLinkClass = 'flex max-w-full flex-1 basis-0 items-center justify-center border-e px-3 py-5 text-center text-gray-700 transition-colors last:border-e-0 hover:text-primary'
const navigationIcon = { size: 18, stroke: 1.5 }

const navigationPopover = (neighbour: BlogEntryNavigation) => (
  <>
    <h6 className="mb-0 text-sm leading-[1.2] font-semibold">
      {neighbour.title}
    </h6>
    <span className="block text-xs text-muted">
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
      <div className="container pb-12">
        <div className="flex justify-center pt-12 md:mt-2">
          <div className="w-full lg:w-3/4">
            <div className="-mt-1 flex flex-wrap items-center justify-between pb-6">
              <div className="mb-2 flex items-center text-sm">
                <BlogEntryAuthor entry={entry} wide />
              </div>
            </div>
            <div className={contentClass()} dangerouslySetInnerHTML={{ __html: entry.content }}></div>
            <div className="mb-1 flex flex-wrap justify-between pt-2 pb-6">
              <div className="me-4 mt-4">
                {entry.tags && entry.tags.map((tag) => (
                  <Link className={`${tagClass()} me-2 mb-2`} href={`/blog/tags/${encodeURIComponent(tag)}/`} key={tag}>
                    #{tag}
                  </Link>
                ))}
              </div>
            </div>
            <nav className="flex rounded-lg border bg-white" aria-label="Навигация по записям">
              {entry.navigation.previous && (
                <Tooltip popover content={navigationPopover(entry.navigation.previous)}>
                  <Link className={navigationLinkClass} href={entry.navigation.previous.urls.canonical} aria-label="Предыдущая запись">
                    <IconChevronLeft {...navigationIcon} className="me-2" />
                    <span className="hidden sm:inline">Предыдущая запись</span>
                  </Link>
                </Tooltip>
              )}
              <Link className={navigationLinkClass} href="/blog/entries/" aria-label="Все записи">
                <IconList {...navigationIcon} className="me-2" />
                <span className="hidden sm:inline">Все записи</span>
              </Link>
              {entry.navigation.next && (
                <Tooltip popover content={navigationPopover(entry.navigation.next)}>
                  <Link className={navigationLinkClass} href={entry.navigation.next.urls.canonical} aria-label="Следующая запись">
                    <span className="hidden sm:inline">Следующая запись</span>
                    <IconChevronRight {...navigationIcon} className="ms-2" />
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
