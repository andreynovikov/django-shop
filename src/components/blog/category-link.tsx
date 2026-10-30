import { cache } from 'react'
import Link from 'next/link'

import { loadBlogCategories } from '@/lib/queries'

// Previews link to several categories each, load them all once per render
const getBlogCategories = cache(loadBlogCategories)

export default async function BlogCategoryLink({ id }: { id: number }) {
  const categories = await getBlogCategories()
  const category = categories.find((category) => category.id === id)

  if (category === undefined)
    return null

  return (
    <Link className="blog-entry-meta-link" href={`/blog/categories/${encodeURIComponent(category.slug)}/`}>
      {category.title}
    </Link>
  )
}
