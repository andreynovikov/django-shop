import Link from 'next/link'
import { dehydrate, QueryClient, useQuery } from '@tanstack/react-query'

import PageLayout from '@/components/layout/page'

import type { NextPageWithLayout } from '@/pages/_app'

import { forumKeys, loadTopics } from '@/lib/queries'
import { ForumTopic } from '@/lib/types'


const Topics: NextPageWithLayout = () => {
  const { data, isSuccess } = useQuery<ForumTopic[]>({
    queryKey: forumKeys.topics(),
    queryFn: () => loadTopics()
  })

  return (
    <div className="container py-5 mb-2 mb-md-4">
      <h2>Разделы:</h2>
      <ul>
        {isSuccess && data.map(topic => (
          <li key={topic.id}>
            <Link href={{ pathname: '/oldforum/topic/[id]', query: { id: topic.id } }}>{topic.title}</Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

Topics.getLayout = function getLayout(page) {
  return (
    <PageLayout title="Архив форума">
      {page}
    </PageLayout>
  )
}

export async function getStaticProps() {
  const queryClient = new QueryClient()
  await queryClient.fetchQuery({
    queryKey: forumKeys.topics(),
    queryFn: () => loadTopics()
  })

  return {
    props: {
      dehydratedState: dehydrate(queryClient),
    }
  }
}

export default Topics