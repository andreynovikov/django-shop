import { dehydrate, QueryClient } from '@tanstack/react-query'

import { blogKeys, loadBlogEntries } from '@/lib/queries'

import BlogEntries from './[page]'

export default BlogEntries

export async function getStaticProps() {
  const queryClient = new QueryClient()
  await queryClient.query({
    queryKey: blogKeys.list(1, {}),
    queryFn: () => loadBlogEntries(1),
    staleTime: 60000,
  }).catch(() => {})

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
      currentPage: 1
    }
  }
}
