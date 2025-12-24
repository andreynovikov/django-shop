import Link from 'next/link'

import UserAvatar from '@/components/user/avatar'

import moment from 'moment'

export default function BlogEntryAuthor({ entry, wide = false }) {
  return (
    <>
      <Link className="blog-entry-meta-link text-nowrap" href={entry.urls.canonical}>
        <div className="blog-entry-author-ava">
          <UserAvatar gravatar={entry.author.gravatar} name={entry.author.full_name} size="50" />
        </div>
        {entry.author.full_name}
      </Link>
      <span className="d-none blog-entry-meta-divider"></span>
      <Link className="d-none blog-entry-meta-link" href={entry.urls.canonical}>
        {moment(entry.publication_date).format(wide ? 'LL' : "D MMM 'YY")}
      </Link>
    </>
  )
}
