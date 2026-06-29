import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query'

import PageLayout from '@/components/layout/page'
import BlogEntryPreview from '@/components/blog/entry-preview'
import PageSelector from '@/components/page-selector'

import { blogKeys, loadBlogEntries, loadBlogTags } from '@/lib/queries'

export default function BlogEntries({ tag, currentPage }) {
  const filters = [{ field: 'tags', value: tag }]

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

BlogEntries.getLayout = function getLayout(page) {
  return (
    <PageLayout title={`Архив по тэгу '${page.props.tag}'`}>
      {page}
    </PageLayout>
  )
}

export async function getStaticProps(context) {
  const tag = context.params.tag
  const currentPage = context.params?.page || '1'
  if (currentPage === '1' && context.params?.page) {
    return {
      redirect: {
        destination: '/blog/tags/' + tag,
        permanent: false
      }
    }
  }

  const filters = [{ field: 'tags', value: tag }]
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
  const tags = await loadBlogTags()
  const entries = await loadBlogEntries(null, null) // just to get current page size
  const pageSize = entries.pageSize
  const paths = tags.reduce((paths, tag) => {
    const pages = Math.ceil(tag.count / pageSize)
    for (let page = 2; page <= pages; page++)
      paths.push({
        params: {
          tag: tag.name,
          page: String(page)
        },
      })
    return paths
  }, [])
  return { paths, fallback: 'blocking' }
}
