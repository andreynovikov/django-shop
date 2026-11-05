import { cache } from 'react'
import { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import CurrentCatalog from '@/components/current-catalog'
import CategoryProducts, { type CategoryProductsQuery } from '@/components/category/products'

import { HttpError, loadCategories, loadCategory, loadProducts } from '@/lib/queries'
import { Category, CategoryTreeItem } from '@/lib/types'

export const revalidate = 86400 // once a day

const pageSize = 1000
const defaultOrder = 'title'
const baseFilters = {
  enabled: true,
}

const categoryPathname = (path: string[]) => `/catalog/${path.join('/')}/`

// The backend also sends the promo image, it isn't in the shared type
type PromoCategory = Category & {
  promo_image?: string
  promo_image_width?: number
  promo_image_height?: number
}

// Shared by generateMetadata and the page, so the category is fetched once per render.
// The path is joined because cache() compares arguments by identity.
const getCategory = cache(async (uri: string) => {
  try {
    return await loadCategory(uri.split('/')) as PromoCategory
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

  const query: CategoryProductsQuery = {
    filters: { ...baseFilters, categories: category.id },
    order: category.product_order || defaultOrder,
    pageSize,
  }
  const products = await loadProducts(1, query.pageSize, query.filters, query.order)

  return pageContentWrapper({
    title: category.name,
    children: (
      <div className="flex flex-wrap justify-between py-2" style={{ gap: "20px" }}>
        <CurrentCatalog />
        {category.promo_image && (
          <div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={category.promo_image} className="si-category-image" width={category.promo_image_width} height={category.promo_image_height} alt="" />
          </div>
        )}
        {category.children && (
          <ul className="si-category-list text-base sm:order-first">
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
        <CategoryProducts categoryName={category.name} query={query} initialProducts={products} />
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
