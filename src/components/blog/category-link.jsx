import { useQuery } from '@tanstack/react-query'

import Link from 'next/link'

import { blogKeys, loadBlogCategory } from '@/lib/queries'

export default function BlogCategoryLink({ id }) {
  const { data: category, isSuccess } = useQuery({
    queryKey: blogKeys.category(id),
    queryFn: () => loadBlogCategory(id)
  })

  if (!isSuccess)
    return null

  return (
    <Link className="blog-entry-meta-link" href={{ pathname: '/blog/categories/[slug]', query: { slug: category.slug } }}>
      {category.title}
    </Link>
  )
}
