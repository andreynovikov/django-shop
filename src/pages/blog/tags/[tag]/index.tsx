import { GetStaticPropsContext } from 'next/types'
import { ParsedUrlQuery } from 'querystring'
import { dehydrate, QueryClient } from '@tanstack/react-query'

import { blogKeys, loadBlogEntries, loadBlogTags } from '@/lib/queries'

import BlogEntries from './[page]'

export default BlogEntries

interface IParams extends ParsedUrlQuery {
  tag: string
}

export async function getStaticProps(context: GetStaticPropsContext<IParams>) {
  const tag = context.params?.tag ?? ''
  const filters = { 'tags': tag }
  const queryClient = new QueryClient()
  await queryClient.prefetchQuery({
    queryKey: blogKeys.list(1, filters),
    queryFn: () => loadBlogEntries(1, filters)
  })

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
      tag,
      currentPage: 1
    }
  }
}

export async function getStaticPaths() {
  const paths: Array<{params: IParams}> = []

  if (process.env.NODE_ENV === 'production' && process.env.PLAYWRIGHT_TEST !== 'true') {
    const tags = await loadBlogTags()
    paths.push(...tags.map((tag) => ({
      params: { tag: tag.name }
    })))
  }
  return { paths, fallback: 'blocking' }
}
