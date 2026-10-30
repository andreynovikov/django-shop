import Link from 'next/link'

import { loadTopics } from '@/lib/queries'

export default async function Topics() {
  const topics = await loadTopics()

  return (
    <div className="container py-5 mb-2 mb-md-4">
      <h2>Разделы:</h2>
      <ul>
        {topics.map(topic => (
          <li key={topic.id}>
            <Link href={`/oldforum/topic/${topic.id}/`}>{topic.title}</Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
