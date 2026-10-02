import { ForumThread, ForumTopic } from '@/lib/types'
import { apiFetch } from './fetch'

export const forumKeys = {
  all: ['forum'],
  topics: () => [...forumKeys.all, 'topics'],
  topic: (topic: string) => [...forumKeys.topics(), topic],
  threads: () => [...forumKeys.all, 'threads'],
  thread: (thread: string) => [...forumKeys.threads(), thread],
}

export async function loadTopics() {
  return await apiFetch<ForumTopic[]>('forum/topics/')
}

export async function loadTopic(id: string) {
  return await apiFetch<ForumTopic>(`forum/topics/${id}/`)
}

export async function loadThread(id: string) {
  return await apiFetch<ForumThread>(`forum/threads/${id}/`)
}