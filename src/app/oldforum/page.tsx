import Link from 'next/link'

import { loadTopics } from '@/lib/queries'

export default async function Topics() {
  const topics = await loadTopics()

  return (
    <div className="container mb-2 py-12 md:mb-6">
      <h2 className="mb-3 text-h2">Разделы:</h2>
      <ul className="mb-4 list-disc ps-8">
        {topics.map(topic => (
          <li key={topic.id}>
            <Link href={`/oldforum/topic/${topic.id}/`}>{topic.title}</Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
