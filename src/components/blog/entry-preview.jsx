import { Fragment } from 'react'
import Link from 'next/link'

import BlogEntryAuthor from '@/components/blog/entry-author'
import BlogCategoryLink from '@/components/blog/category-link'

export default function BlogEntryPreview({ entry, last }) {
  const previewContent = () => {
    return entry.content.preview.replace('<!--more-->', `
            <a href="${entry.urls.canonical}" class="blog-entry-meta-link fw-medium">[читать далее]</a>
        `)
  }

  return (
    <article className={"blog-list pb-4 mb-5" + (!last && " border-bottom")}>
      <div className="blog-start-column">
        <div className="d-flex align-items-center fs-sm pb-2 mb-1">
          <BlogEntryAuthor entry={entry} />
        </div>
        <h2 className="h5 blog-entry-title">
          <Link href={entry.urls.canonical}>{entry.title}</Link>
        </h2>
      </div>
      <div className="blog-end-column">
        { /* <a className="blog-entry-thumb mb-3" href="blog-single.html"><img src="img/blog/02.jpg" alt="Post" /></a> */}
        <div className="d-flex align-items-baseline justify-content-between mb-1">
          <div className="fs-sm text-muted pe-2 mb-2">
            {entry.categories && entry.categories.map((id, index) => (
              <Fragment key={id}>
                {index > 0 && ', '}
                <BlogCategoryLink id={id} />
              </Fragment>
            ))}
          </div>
          <div className="font-size-sm mb-2">
            {entry.tags && entry.tags.map((tag) => (
              <Link className="btn-tag ms-2" href={{ pathname: '/blog/tags/[tag]', query: { tag } }} key={tag}>
                #{tag}
              </Link>
            ))}
          </div>
        </div>
        <div className="fs-sm">
          <div dangerouslySetInnerHTML={{ __html: previewContent() }}></div>
        </div>
      </div>
    </article>
  )
}
