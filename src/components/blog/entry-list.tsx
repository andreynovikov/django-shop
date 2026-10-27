import BlogEntryPreview from '@/components/blog/entry-preview'
import PageSelector from '@/components/page-selector'

import { BlogEntryInfo, PaginatedResult } from '@/lib/types'

interface BlogEntryListProps {
  entries: PaginatedResult<BlogEntryInfo>
  pathname: string  // path of the first page, the page number is appended to it
}

export default function BlogEntryList({ entries, pathname }: BlogEntryListProps) {
  return (
    <div className="row justify-content-center pt-5 mt-2">
      <section className="col-lg-9">
        {entries.results.map((entry, index) => (
          <BlogEntryPreview entry={entry} last={index === entries.results.length - 1} key={entry.id} />
        ))}

        {entries.totalPages > 1 && (
          <>
            <hr className="my-3" />
            <PageSelector
              pathname={pathname}
              pageInPath
              totalPages={entries.totalPages}
              currentPage={entries.currentPage} />
          </>
        )}
      </section>
    </div>
  )
}
