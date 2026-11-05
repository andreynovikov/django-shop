import { cache } from 'react'
import { Metadata } from 'next'
import { notFound } from 'next/navigation'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import ProductCard from '@/components/product/card'

import { HttpError, loadCategories, loadCategory, loadProducts } from '@/lib/queries'
import { CategoryTreeItem } from '@/lib/types'

export const revalidate = 86400 // once a day

const pageSize = 1000
const defaultOrder = 'title'
const baseFilters = {
  enabled: true,
}

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

export async function generateMetadata({ params }: PageProps<'/catalog/[...path]'>): Promise<Metadata> {
  const { path } = await params
  const category = await getCategory(path.join('/'))

  return {
    title: category.name,
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
      <div className="container mb-5">
        <div className="row">
          <div className="products-grid col-12 sidebar-none">
            <div className="row">
              {products.results.map((product) => (
                <div className="col-lg-4 col-sm-6" key={product.id}>
                  <ProductCard product={product} />
                </div>
              ))}
            </div>
          </div>
        </div>
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
