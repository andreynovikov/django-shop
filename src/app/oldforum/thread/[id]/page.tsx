import { notFound } from 'next/navigation'

import { HttpError, loadThread } from '@/lib/queries'

async function getThread(id: string) {
  try {
    return await loadThread(id)
  } catch (err) {
    if (err instanceof HttpError && err.status === 404)
      notFound()
    throw err
  }
}

export default async function Thread({ params }: PageProps<'/oldforum/thread/[id]'>) {
  const { id } = await params
  const thread = await getThread(id)

  return (
    <div className="container py-5 mb-2 mb-md-4">
      <h2>{thread.title}</h2>
      <div className="mt-5">
        {thread.opinions.map(opinion => (
          <div key={opinion.id} className="border-top py-2">
            <div className="opacity-50 fs-xs text-end pb-1">
              {opinion.post && (
                new Date(opinion.post).toLocaleString('ru', { timeZone: 'Europe/Moscow' })
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

// The archive never changes: render each thread on first visit and keep it cached
export async function generateStaticParams() {
  return []
}
