import { cache } from 'react'
import { Metadata } from 'next'
import { notFound } from 'next/navigation'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'

import { HttpError, loadPage, loadPages } from '@/lib/queries'

// help and dialog pages are shown inside other pages, not on their own
const isEmbedded = (uri: string[]) => ['help', 'dialog'].includes(uri[0])

// Only prerendered pages are served, unknown uris get 404 before rendering
export const dynamicParams = false

// Shared by generateMetadata and the page, so the page is fetched once per render
const getPage = cache(async (uri: string[]) => {
  try {
    return await loadPage(uri)
  } catch (err) {
    if (err instanceof HttpError && err.status === 404)
      notFound()
    throw err
  }
})

export async function generateMetadata({ params }: PageProps<'/pages/[...uri]'>): Promise<Metadata> {
  const { uri } = await params
  const page = await getPage(uri)
  return { title: page.title }
}

export default async function FlatPage({ params }: PageProps<'/pages/[...uri]'>) {
  const { uri } = await params
  const page = await getPage(uri)

  return pageContentWrapper({
    title: page.title,
    children: (
      <div className="container py-5 mb-2 mb-md-4">
        <div dangerouslySetInnerHTML={{ __html: page.content }}></div>
      </div>
    )
  })
}

export async function generateStaticParams() {
  if (process.env.NODE_ENV !== 'production' || process.env.PLAYWRIGHT_TEST === 'true')
    return []

  const pages = await loadPages()
  return pages
    .map(page => page.url.slice(1, -1).split('/'))
    .filter(uri => !isEmbedded(uri))
    .map(uri => ({ uri }))
}
