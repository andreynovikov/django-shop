import { ReactElement } from 'react'
import { ParsedUrlQuery } from 'querystring'
import Link from 'next/link'
import { GetStaticPropsContext } from 'next/types'
import { QueryClient } from '@tanstack/react-query'

import PageLayout from '@/components/layout/page'
import BlogEntryAuthor from '@/components/blog/entry-author'
import Tooltip from '@/components/ui/tooltip'

import { HttpError, blogKeys, loadBlogEntries, loadBlogEntry } from '@/lib/queries'
import { BlogEntry } from '@/lib/types'

import moment from 'moment'

export default function BlogEntryPage({ entry }: { entry: BlogEntry }) {
  const previousPopover = entry.navigation.previous && (
    <>
      <h6 className="fs-sm fw-semibold mb-0">
        {entry.navigation.previous.title}
      </h6>
      <span className="d-block fs-xs text-muted">
        {entry.navigation.previous.author.full_name}
      </span>
    </>
  )
  const nextPopover = entry.navigation.next && (
    <>
      <h6 className="fs-sm fw-semibold mb-0">
        {entry.navigation.next.title}
      </h6>
      <span className="d-block fs-xs text-muted">
        {entry.navigation.next.author.full_name}
      </span>
    </>
  )

  return (
    <div className="container pb-5">
      <div className="row justify-content-center pt-5 mt-md-2">
        <div className="col-lg-9">
          <div className="d-flex flex-wrap justify-content-between align-items-center pb-4 mt-n1">
            <div className="d-flex align-items-center fs-sm mb-2">
              <BlogEntryAuthor entry={entry} wide />
            </div>
          </div>
          <div dangerouslySetInnerHTML={{ __html: entry?.content }}></div>
          <div className="d-flex flex-wrap justify-content-between pt-2 pb-4 mb-1">
            <div className="mt-3 me-3">
              {entry.tags && entry.tags.map((tag) => (
                <Link className="btn-tag me-2 mb-2" href={{ pathname: '/blog/tags/[tag]', query: { tag } }} key={tag}>
                  #{tag}
                </Link>
              ))}
            </div>
          </div>
          <nav className="entry-navigation" aria-label="Навигация по записям">
            {entry.navigation.previous && (
              <Tooltip popover content={previousPopover}>
                <Link className="entry-navigation-link" href={entry.navigation.previous.urls.canonical}>
                  <i className="ci-arrow-left me-2" />
                  <span className="d-none d-sm-inline">Предыдущая запись</span>
                </Link>
              </Tooltip>
            )}
            <Link className="entry-navigation-link" href="/blog/entries">
              <i className="ci-view-list me-2" />
              <span className="d-none d-sm-inline">Все записи</span>
            </Link>
            {entry.navigation.next && (
              <Tooltip popover content={nextPopover}>
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
}
interface PageParams {
  entry: BlogEntry
}

BlogEntryPage.getLayout = function getLayout(page: ReactElement, pageProps: PageParams) {
  return (
    <PageLayout title={pageProps.entry.title}>
      {page}
    </PageLayout>
  )
}

interface IParams extends ParsedUrlQuery {
  entry: string[]
}

export async function getStaticProps(context: GetStaticPropsContext<IParams>) {
  const uri = context.params?.entry ?? []

  const queryClient = new QueryClient()
  try {
    const entry = await queryClient.query({
      queryKey: blogKeys.detail(uri),
      queryFn: () => loadBlogEntry(uri)
    })
    // backend returns an empty entry instead of 404 for unknown uri
    if (!entry?.id)
      return {
        notFound: true,
      }

    if (uri.length === 1)
      return {
        redirect: {
          destination: entry.urls.canonical,
          permanent: false,
        },
      }

    return {
      props: {
        entry
      }
    }
  } catch (error) {
    if (error instanceof HttpError && error.response.status === 404) {
      return {
        notFound: true,
      }
    } else {
      throw error
    }
  }
}

export async function getStaticPaths() {
  const paths: Array<{params: IParams}> = []

  if (process.env.NODE_ENV === 'production' && process.env.PLAYWRIGHT_TEST !== 'true') {
    let page: number | undefined = 1
    while (page !== undefined) {
      const entries = await loadBlogEntries(page)
      paths.push(...entries.results.map((entry) => {
        const date = moment(entry.publication_date)
        return {
          params: {
            entry: [
              String(date.year()),
              String(date.month() + 1).padStart(2, '0'),
              String(date.date()).padStart(2, '0'),
              entry.slug
            ]
          }
        }
      }))
      if (entries.totalPages > entries.currentPage)
        page += 1
      else
        page = undefined
    }
  }
  return { paths, fallback: 'blocking' } // we use blocking to generate new entries without rebuilding
}
