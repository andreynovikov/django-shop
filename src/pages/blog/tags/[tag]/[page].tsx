import { ReactElement } from 'react'
import { GetStaticPropsContext } from 'next/types'
import { ParsedUrlQuery } from 'querystring'
import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query'

import PageLayout from '@/components/layout/page'
import BlogEntryPreview from '@/components/blog/entry-preview'
import PageSelector from '@/components/page-selector'

import { blogKeys, loadBlogEntries, loadBlogTags } from '@/lib/queries'

interface PageParams {
  tag: string
  currentPage: number
}

export default function BlogEntries({ tag, currentPage }: PageParams) {
  const filters = { 'tags': tag }

  const { data: entries, isSuccess } = useQuery({
    queryKey: blogKeys.list(currentPage, filters),
    queryFn: () => loadBlogEntries(currentPage, filters)
  })

  if (isSuccess)
    return (
      <div className="container pb-5 mb-2 mb-md-4">
        <div className="row justify-content-center pt-5 mt-2">
          <section className="col-lg-9">
            {entries.results.map((entry, index) => (
              < BlogEntryPreview entry={entry} last={index === entries.results.length - 1} key={entry.id} />
            ))}

            {entries.totalPages > 1 && (
              <>
                <hr className="my-3" />
                <PageSelector
                  pathname="/blog/tags/[tag]/[page]"
                  path={[]}
                  pathExtra={{ tag }}
                  totalPages={entries.totalPages}
                  currentPage={entries.currentPage} />
              </>
            )}
          </section>
        </div>
      </div>
    )

  return null
}

BlogEntries.getLayout = function getLayout(page: ReactElement, pageProps: PageParams) {
  return (
    <PageLayout title={`Архив по тэгу '${pageProps.tag}'`}>
      {page}
    </PageLayout>
  )
}

interface IParams extends ParsedUrlQuery {
  tag: string
  page: string
}

export async function getStaticProps(context: GetStaticPropsContext<IParams>) {
  const tag = context.params?.tag ?? ''
  const currentPage = +(context.params?.page || '1')
  if (currentPage === 1 && context.params?.page) {
    return {
      redirect: {
        destination: '/blog/tags/' + tag,
        permanent: false
      }
    }
  }

  const filters = { 'tags': tag }
  const queryClient = new QueryClient()
  await queryClient.prefetchQuery({
    queryKey: blogKeys.list(currentPage, filters),
    queryFn: () => loadBlogEntries(currentPage, filters)
  })

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
      tag,
      currentPage
    }
  }
}

export async function getStaticPaths() {
  const paths: Array<{params: IParams}> = []

  if (process.env.NODE_ENV === 'production' && process.env.PLAYWRIGHT_TEST !== 'true') {
    const tags = await loadBlogTags()
    const entries = await loadBlogEntries(null) // just to get current page size
    const pageSize = entries.pageSize
    paths.push(...tags.reduce<Array<{params: IParams}>>((paths, tag) => {
      const pages = Math.ceil(tag.count / pageSize)
      for (let page = 2; page <= pages; page++)
        paths.push({
          params: {
            tag: tag.name,
            page: String(page)
          },
        })
      return paths
    }, []))
  }
  return { paths, fallback: 'blocking' }
}
