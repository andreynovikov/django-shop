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
    <div className="container mb-2 py-12 md:mb-6">
      <h2 className="mb-3 text-h2">{thread.title}</h2>
      <div className="mt-12">
        {thread.opinions.map(opinion => (
          <div key={opinion.id} className="border-t py-2">
            <div className="pb-1 text-end text-xs opacity-50">
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
