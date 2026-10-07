import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query'

import PageLayout from '@/components/layout/page'
import BlogEntryPreview from '@/components/blog/entry-preview'
import PageSelector from '@/components/page-selector'

import { blogKeys, loadBlogEntries } from '@/lib/queries'

import range from 'lodash/range'

export default function BlogEntries({ currentPage }) {

  const { data: entries, isSuccess } = useQuery({
    queryKey: blogKeys.list(currentPage, null),
    queryFn: () => loadBlogEntries(currentPage, null)
  })

  if (isSuccess)
    return (
      <div className="container pb-5 mb-2 mb-md-4">
        { /* TODO: add featured posts carousel */}
        <hr className="mt-5" />
        <div className="row justify-content-center pt-5 mt-2">
          <section className="col-lg-9">
            {entries.results.map((entry, index) => (
              < BlogEntryPreview entry={entry} last={index === entries.results.length - 1} key={entry.id} />
            ))}

            {entries.totalPages > 1 && (
              <>
                <hr className="my-3" />
                <PageSelector
                  pathname="/blog/entries/[page]"
                  path={[]}
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

BlogEntries.getLayout = function getLayout(page) {
  return (
    <PageLayout title="Блог">
      {page}
    </PageLayout>
  )
}

export async function getStaticProps(context) {
  const currentPage = +(context.params?.page || '1')
  if (currentPage === 1 && context.params?.page) {
    return {
      redirect: {
        destination: '/blog/entries/',
        permanent: false
      }
    }
  }

  const queryClient = new QueryClient()
  await queryClient.query({
    queryKey: blogKeys.list(currentPage, null),
    queryFn: () => loadBlogEntries(currentPage, null),
    staleTime: 60000,
  }).catch(() => {})

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
      currentPage
    }
  }
}

export async function getStaticPaths() {
  const paths = []

  if (process.env.NODE_ENV === 'production' && process.env.PLAYWRIGHT_TEST !== 'true') {
    const entries = await loadBlogEntries(null, null)
    const pages = Math.ceil(entries.count / entries.pageSize)
    paths.push(...range(2, pages + 1).map((page) => ({
      params: { page: String(page) }
    })))
  }
  return { paths, fallback: false }
}
