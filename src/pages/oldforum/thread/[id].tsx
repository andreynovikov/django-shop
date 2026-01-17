import { GetServerSideProps } from 'next'
import { useRouter } from 'next/router'
import { useQuery } from '@tanstack/react-query'

import PageLayout from '@/components/layout/page'

import type { NextPageWithLayout } from '@/pages/_app'

import { forumKeys, loadThread } from '@/lib/queries'
import { ForumThread } from '@/lib/types'


const Thread: NextPageWithLayout = () => {
    const router = useRouter()
    const { data, isSuccess } = useQuery<ForumThread>({
        queryKey: forumKeys.thread(router.query.id),
        queryFn: () => loadThread(router.query.id)
    })

    if (!isSuccess)
        return null

    return (
        <div className="container py-5 mb-2 mb-md-4">
            <h2>{data.title}</h2>
            <div className="mt-5">
                {data.opinions.map(opinion => (
                    <div key={opinion.id} className="border-top py-2">
                        <div className="opacity-50 fs-xs text-end pb-1">
                            {opinion.post && (
                                new Date(opinion.post).toLocaleString()
                            )}
                        </div>
                        <div>
                            {opinion.text}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

Thread.getLayout = function getLayout(page) {
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

export default Thread