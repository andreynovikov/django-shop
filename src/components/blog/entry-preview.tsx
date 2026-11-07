import { Fragment } from 'react'
import Link from 'next/link'

import BlogEntryAuthor from '@/components/blog/entry-author'
import BlogCategoryLink, { metaLinkClass } from '@/components/blog/category-link'
import { contentClass } from '@/components/ui/content'
import { tagClass } from '@/components/ui/widget'

import { BlogEntryInfo } from '@/lib/types'

interface BlogEntryPreviewProps {
  entry: BlogEntryInfo
  last: boolean
}

export default function BlogEntryPreview({ entry, last }: BlogEntryPreviewProps) {
  const previewContent = () => {
    return entry.content.preview.replace('<!--more-->', `
            <a href="${entry.urls.canonical}" class="${metaLinkClass} font-medium">[читать далее]</a>
        `)
  }

  return (
    <article className={`mb-12 pb-6 md:flex ${last ? "" : "border-b"}`}>
      <div className="md:w-[37%] md:pe-[.9375rem]">
        <div className="mb-1 flex items-center pb-2 text-sm">
          <BlogEntryAuthor entry={entry} />
        </div>
        <h2 className="mb-3 text-h5">
          <Link className="leading-[1.3] text-heading hover:text-primary" href={entry.urls.canonical}>{entry.title}</Link>
        </h2>
      </div>
      <div className="md:w-[63%] md:ps-[.9375rem]">
        <div className="mb-1 flex items-baseline justify-between">
          <div className="mb-2 pe-2 text-sm text-muted">
            {entry.categories && entry.categories.map((id, index) => (
              <Fragment key={id}>
                {index > 0 && ', '}
                <BlogCategoryLink id={id} />
              </Fragment>
            ))}
          </div>
          <div className="mb-2 text-sm">
            {entry.tags && entry.tags.map((tag) => (
              <Link className={`${tagClass()} ms-2`} href={`/blog/tags/${encodeURIComponent(tag)}/`} key={tag}>
                #{tag}
              </Link>
            ))}
          </div>
        </div>
        <div className={contentClass({ size: 'sm' })} dangerouslySetInnerHTML={{ __html: previewContent() }}></div>
      </div>
    </article>
  )
}
