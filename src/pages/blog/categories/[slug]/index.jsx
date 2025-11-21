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
  const filters = [{ field: 'categories', value: category.id }]
  await queryClient.prefetchQuery({
    queryKey: blogKeys.list('1', filters),
    queryFn: () => loadBlogEntries('1', filters)
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
  const categories = await loadBlogCategories()
  const paths = categories.map((category) => ({
    params: { slug: category.slug }
  }))
  return { paths, fallback: 'blocking' }
}
