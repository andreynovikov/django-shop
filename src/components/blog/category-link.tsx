import { cache } from 'react'
import Link from 'next/link'

import { loadBlogCategories } from '@/lib/queries'

// A link in the details of a blog entry: its author, date and categories
export const metaLinkClass = 'inline-block text-muted hover:text-gray-700'

// Previews link to several categories each, load them all once per render
const getBlogCategories = cache(loadBlogCategories)

export default async function BlogCategoryLink({ id }: { id: number }) {
  const categories = await getBlogCategories()
  const category = categories.find((category) => category.id === id)

  if (category === undefined)
    return null

  return (
    <Link className={metaLinkClass} href={`/blog/categories/${encodeURIComponent(category.slug)}/`}>
      {category.title}
    </Link>
  )
}
