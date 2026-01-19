import { GetServerSideProps } from 'next'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'

import PageLayout from '@/components/layout/page'

import type { NextPageWithLayout } from '@/pages/_app'

import { forumKeys, loadTopic } from '@/lib/queries'
import { ForumTopic } from '@/lib/types'


const Topic: NextPageWithLayout = () => {
  const router = useRouter()
  const { data, isSuccess } = useQuery<ForumTopic>({
    queryKey: forumKeys.topic(router.query.id),
    queryFn: () => loadTopic(router.query.id)
  })

  if (!isSuccess)
    return null

  return (
    <div className="container py-5 mb-2 mb-md-4">
      <h2>{data.title}</h2>
      <ul>
        {data.threads.map(thread => (
          <li key={thread.id}>
            <Link href={{ pathname: '/oldforum/thread/[id]', query: { id: thread.id } }}>{thread.title}</Link>
            { thread.mtime && (
              <>
                {" "}&mdash;{" "}
                { new Date(thread.mtime).toLocaleDateString('ru') }
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

Topic.getLayout = function getLayout(page) {
  return (
    <PageLayout title="Архив форума">
      {page}
    </PageLayout>
  )
}

export const getServerSideProps = (async (context) => {
  context.res.setHeader(
    'Cache-Control',
    's-maxage=31536000'
  )
 
  return {
    props: {},
  }
}) satisfies GetServerSideProps

export default Topic