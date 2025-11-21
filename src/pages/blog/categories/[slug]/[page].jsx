import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query'

import PageLayout from '@/components/layout/page'
import BlogEntryPreview from '@/components/blog/entry-preview'
import PageSelector from '@/components/page-selector'

import { blogKeys, loadBlogEntries, loadBlogCategories, loadBlogCategory } from '@/lib/queries'

export default function BlogEntries({ category, currentPage }) {
  const filters = [{ field: 'categories', value: category.id }]

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
                  pathname="/blog/categories/[slug]/[page]"
                  path={[]}
                  pathExtra={{ slug: category.slug }}
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
    <PageLayout title={`Архив категории ${page.props.category.title}`}>
      {page}
    </PageLayout>
  )
}

export async function getStaticProps(context) {
  const slug = context.params.slug
  const currentPage = context.params?.page || '1'
  if (currentPage === '1' && context.params?.page) {
    return {
      redirect: {
        destination: '/blog/categories/' + slug,
        permanent: false
      }
    }
  }

  const queryClient = new QueryClient()
  const category = await queryClient.fetchQuery({
    queryKey: blogKeys.category(slug),
    queryFn: () => loadBlogCategory(slug)
  })
  const filters = [{ field: 'categories', value: category.id }]
  await queryClient.prefetchQuery({
    queryKey: blogKeys.list(currentPage, filters),
    queryFn: () => loadBlogEntries(currentPage, filters)
  })

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
      category,
      currentPage
    }
  }
}

export async function getStaticPaths() {
  const categories = await loadBlogCategories()
  const entries = await loadBlogEntries(null, null) // just to get current page size
  const pageSize = entries.pageSize
  const paths = categories.reduce((paths, category) => {
    const pages = Math.ceil(category.count / pageSize)
    for (let page = 2; page <= pages; page++)
      paths.push({
        params: {
          slug: category.slug,
          page: String(page)
        },
      })
    return paths
  }, [])
  return { paths, fallback: 'blocking' }
}
