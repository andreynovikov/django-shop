import { cache } from 'react'
import { Metadata } from 'next'
import { notFound } from 'next/navigation'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import ProductCard from '@/components/product/card'

import { baseFilters } from '@/lib/catalog'
import { HttpError, loadCategories, loadCategory, loadCurrentSite, loadProducts } from '@/lib/queries'
import { CategoryTreeItem } from '@/lib/types'

export const revalidate = 3600

const pageSize = 1000
const defaultOrder = 'title'

// Shared by generateMetadata and the page, so the category is fetched once per render.
// The path is joined because cache() compares arguments by identity.
const getCategory = cache(async (uri: string) => {
  try {
    return await loadCategory(uri.split('/'))
  } catch (err) {
    if (err instanceof HttpError && err.status === 404)
      notFound()
    throw err
  }
})

const getSite = cache(loadCurrentSite)

export async function generateMetadata({ params }: PageProps<'/catalog/[...path]'>): Promise<Metadata> {
  const { path } = await params
  const [category, site] = await Promise.all([getCategory(path.join('/')), getSite()])

  return {
    title: category.name,
    description: [...category.path.breadcrumbs].reverse().map(({ name }) => name).concat(site.title).join(' - '),
  }
}

export default async function CategoryPage({ params }: PageProps<'/catalog/[...path]'>) {
  const { path } = await params
  const category = await getCategory(path.join('/'))

  const filters = { ...baseFilters, categories: category.id }
  const products = await loadProducts(1, pageSize, filters, category.product_order || defaultOrder)

  return pageContentWrapper({
    title: category.name,
    description: category.description,
    children: (
      <div className="container mb-12 grid gap-x-6 sm:grid-cols-2 lg:grid-cols-3">
        {products.results.map((product) => (
          <ProductCard product={product} key={product.id} />
        ))}
      </div>
    )
  })
}

export async function generateStaticParams() {
  if (process.env.NODE_ENV !== 'production' || process.env.PLAYWRIGHT_TEST === 'true')
    return []

  const collectPaths = (categories: CategoryTreeItem[], parent: string[]): string[][] =>
    categories.flatMap((category) => {
      const path = [...parent, category.slug]
      return [path, ...collectPaths(category.children ?? [], path)]
    })

  return collectPaths(await loadCategories(), []).map((path) => ({ path }))
}
