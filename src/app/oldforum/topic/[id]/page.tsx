import Link from 'next/link'
import { notFound } from 'next/navigation'

import { HttpError, loadTopic } from '@/lib/queries'

async function getTopic(id: string) {
  try {
    return await loadTopic(id)
  } catch (err) {
    if (err instanceof HttpError && err.status === 404)
      notFound()
    throw err
  }
}

export default async function Topic({ params }: PageProps<'/oldforum/topic/[id]'>) {
  const { id } = await params
  const topic = await getTopic(id)

  return (
    <div className="container py-5 mb-2 mb-md-4">
      <h2>{topic.title}</h2>
      <ul>
        {topic.threads.map(thread => (
          <li key={thread.id}>
            <Link href={`/oldforum/thread/${thread.id}/`}>{thread.title}</Link>
            { thread.mtime && (
              <>
                {" "}&mdash;{" "}
                { new Date(thread.mtime).toLocaleDateString('ru', { timeZone: 'Europe/Moscow' }) }
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

// The archive never changes: render each topic on first visit and keep it cached
export async function generateStaticParams() {
  return []
}
