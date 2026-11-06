import { cache } from 'react'
import { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import CurrentCatalog from '@/components/current-catalog'
import CategoryProducts, { type CategoryProductsQuery } from '@/components/category/products'

import { HttpError, loadCategories, loadCategory, loadProducts } from '@/lib/queries'
import { CategoryTreeItem } from '@/lib/types'

export const revalidate = 86400 // once a day

// all products of the category are on one page
const pageSize = 1000
const defaultOrder = 'title'
const baseFilters = {
  enabled: true,
}

const categoryPathname = (path: string[]) => `/catalog/${path.join('/')}/`

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

// The load time goes to the browser, which loads the list again once it is stale
async function loadCategoryProducts({ filters, order, pageSize }: CategoryProductsQuery) {
  const products = await loadProducts(1, pageSize, filters, order)
  return { products, loadedAt: Date.now() }
}

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

  const query: CategoryProductsQuery = {
    filters: { ...baseFilters, categories: category.id },
    order: category.product_order || defaultOrder,
    pageSize,
  }
  const { products, loadedAt } = await loadCategoryProducts(query)

  return pageContentWrapper({
    title: category.name,
    children: (
      <div className="container">
        <CurrentCatalog />
        {category.children && (
          <ul className="mb-4 list-disc ps-8">
            { /* TODO: filter hidden (here or in API) */}
            {category.children.map((subcategory) => (
              <li key={subcategory.id}>
                <Link href={categoryPathname([...path, subcategory.slug])}>
                  {subcategory.name}
                </Link>
              </li>
            ))}
          </ul>
        )}
        <CategoryProducts categoryName={category.name} query={query} initialProducts={products} loadedAt={loadedAt} />
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
