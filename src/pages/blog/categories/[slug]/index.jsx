import { dehydrate, QueryClient } from '@tanstack/react-query'

import { blogKeys, loadBlogEntries, loadBlogCategories, loadBlogCategory } from '@/lib/queries'

import BlogEntries from './[page]'

export default BlogEntries

export async function getStaticProps(context) {
  const slug = context.params.slug
  const queryClient = new QueryClient()
  const category = await queryClient.fetchQuery({
    queryKey: blogKeys.category(slug),
    queryFn: () => loadBlogCategory(slug)
  })
  const filters = { categories: category.id }
  await queryClient.prefetchQuery({
    queryKey: blogKeys.list(1, filters),
    queryFn: () => loadBlogEntries(1, filters)
  })

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
      category,
      currentPage: '1'
    }
  }
}

export async function getStaticPaths() {
  const paths = []

  if (process.env.NODE_ENV === 'production' && process.env.PLAYWRIGHT_TEST !== 'true') {
    const categories = await loadBlogCategories()
    paths.push(...categories.map((category) => ({
      params: { slug: category.slug }
    })))
  }
  return { paths, fallback: 'blocking' }
}
