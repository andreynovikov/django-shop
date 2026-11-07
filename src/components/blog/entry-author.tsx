import Link from 'next/link'

import UserAvatar from '@/components/user/avatar'
import { metaLinkClass } from '@/components/blog/category-link'

import { BlogEntry, BlogEntryInfo } from '@/lib/types'

import moment from 'moment'

interface BlogEntryAuthorProps {
  entry: BlogEntry | BlogEntryInfo
  wide?: boolean
}

export default function BlogEntryAuthor({ entry, wide = false }: BlogEntryAuthorProps) {
  return (
    <>
      <Link className={`${metaLinkClass} whitespace-nowrap`} href={entry.urls.canonical}>
        <div className="me-2 inline-block size-8 rounded-full border p-0.5 align-middle [&>img]:h-auto [&>img]:w-full">
          <UserAvatar gravatar={entry.author.gravatar} name={entry.author.full_name} size={50} />
        </div>
        {entry.author.full_name}
      </Link>
      <span className="mx-4 hidden h-4 w-px bg-[#d9e1e9] align-middle"></span>
      <Link className="hidden text-muted hover:text-gray-700" href={entry.urls.canonical}>
        {moment(entry.publication_date).format(wide ? 'LL' : "D MMM 'YY")}
      </Link>
    </>
  )
}
